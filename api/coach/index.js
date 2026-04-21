/**
 * Vercel Serverless Function: /api/coach
 *
 * Strategy-specific coaching via Claude API.
 * Dormant for personal use (use "Review with Claude" copy-paste flow).
 * Ready for commercialization — just set ANTHROPIC_API_KEY env var.
 *
 * Request body:
 *   { strategy: string, message: string, history: [{role, content}], tradeContext?: string }
 *
 * Environment variables:
 *   ANTHROPIC_API_KEY — Claude API key (required)
 *   COACH_ENABLED     — set to "true" to enable (default: disabled)
 *   ALLOWED_ORIGIN    — restrict CORS (default: https://fluxus-dashboard.vercel.app)
 */

export const config = { runtime: 'edge' }

const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || 'https://fluxus-dashboard.vercel.app'

const STRATEGY_PROMPTS = {
  'episodic-pivot': `You are an expert trading coach specializing in Episodic Pivot setups. You help traders identify and execute gap-up breakouts on significant news (earnings, FDA, contracts). Focus on: gap quality, volume confirmation, risk/reward, stop placement, and position sizing. Be direct and specific.`,
  'vcp': `You are an expert trading coach specializing in Volatility Contraction Patterns. You help traders identify bases with decreasing price contractions indicating institutional accumulation. Focus on: contraction count, depth progression, volume dry-up, pivot identification, and breakout timing. Be direct and specific.`,
  'breakout': `You are an expert trading coach specializing in breakout trading. You help traders identify and execute classic breakouts from proper bases — cup with handle, flat base, double bottom. Focus on: base depth/length, volume on breakout, relative strength, and risk management. Be direct and specific.`,
  'monthly-review': `You are a trading coach reviewing monthly performance. Be direct, specific, and actionable. No fluff. Analyze the data provided and give concrete findings, patterns, and suggestions.`,
}

const MAX_MESSAGE_LEN = 5000
const MAX_CONTEXT_LEN = 10000

export default async function handler(req) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders })
  }

  if (req.method !== 'POST') {
    return Response.json({ error: 'Method not allowed' }, { status: 405 })
  }

  if (process.env.COACH_ENABLED !== 'true') {
    return Response.json({
      error: 'Coach API is disabled. Use the "Review with Claude" copy-paste flow, or set COACH_ENABLED=true and ANTHROPIC_API_KEY to enable.',
    }, { status: 503 })
  }

  const apiKey = process.env.ANTHROPIC_API_KEY
  if (!apiKey) {
    return Response.json({ error: 'ANTHROPIC_API_KEY not configured' }, { status: 500 })
  }

  try {
    const { strategy, message, history = [], tradeContext } = await req.json()

    if (!strategy || !message) {
      return Response.json({ error: 'Missing strategy or message' }, { status: 400 })
    }
    if (message.length > MAX_MESSAGE_LEN) {
      return Response.json({ error: 'Message too long' }, { status: 400 })
    }
    if (tradeContext && tradeContext.length > MAX_CONTEXT_LEN) {
      return Response.json({ error: 'Trade context too long' }, { status: 400 })
    }

    const systemPrompt = STRATEGY_PROMPTS[strategy] || STRATEGY_PROMPTS['breakout']
    const contextBlock = tradeContext ? `\n\nTrade context:\n${tradeContext}` : ''

    const messages = [
      ...history.slice(-10),
      { role: 'user', content: message + contextBlock },
    ]

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1024,
        system: systemPrompt,
        messages,
      }),
    })

    if (!response.ok) {
      console.error('Claude API error:', response.status, await response.text())
      return Response.json({ error: `Claude API error: ${response.status}` }, { status: 502 })
    }

    const data = await response.json()
    const reply = data.content?.[0]?.text || 'No response generated.'

    return Response.json({ reply }, { headers: corsHeaders })
  } catch (err) {
    console.error('Coach API error:', err)
    return Response.json({ error: 'Internal server error' }, { status: 500 })
  }
}
