#!/usr/bin/env node

// ============================================================================
// Follow Traders — Central Feed Generator
// ============================================================================
// Runs on GitHub Actions (daily at 22:00 UTC / 07:00 JST) to fetch content
// and publish feed-x.json, feed-podcasts.json, and feed-blogs.json.
//
// Deduplication: tracks previously seen tweet IDs, video IDs, and article
// URLs in state-feed.json so content is never repeated across runs.
//
// Usage: node generate-feed.js [--tweets-only | --podcasts-only | --blogs-only]
// Env vars needed: X_BEARER_TOKEN, SUPADATA_API_KEY
// ============================================================================

import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';

// -- Constants ---------------------------------------------------------------

const SUPADATA_BASE = 'https://api.supadata.ai/v1';
const X_API_BASE = 'https://api.x.com/2';
const TWEET_LOOKBACK_HOURS = 24;
const PODCAST_LOOKBACK_HOURS = 336; // 14 days — podcasts publish weekly/biweekly
const BLOG_LOOKBACK_HOURS = 72;
const MAX_TWEETS_PER_USER = 3;
const MAX_ARTICLES_PER_BLOG = 3;

// State file lives in the repo root so it gets committed by GitHub Actions
const SCRIPT_DIR = decodeURIComponent(new URL('.', import.meta.url).pathname);
const STATE_PATH = join(SCRIPT_DIR, '..', 'state-feed.json');

// -- State Management --------------------------------------------------------

async function loadState() {
  if (!existsSync(STATE_PATH)) {
    return { seenTweets: {}, seenVideos: {}, seenArticles: {} };
  }
  try {
    const state = JSON.parse(await readFile(STATE_PATH, 'utf-8'));
    if (!state.seenArticles) state.seenArticles = {};
    return state;
  } catch {
    return { seenTweets: {}, seenVideos: {}, seenArticles: {} };
  }
}

async function saveState(state) {
  const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
  for (const [id, ts] of Object.entries(state.seenTweets)) {
    if (ts < cutoff) delete state.seenTweets[id];
  }
  for (const [id, ts] of Object.entries(state.seenVideos)) {
    if (ts < cutoff) delete state.seenVideos[id];
  }
  for (const [id, ts] of Object.entries(state.seenArticles || {})) {
    if (ts < cutoff) delete state.seenArticles[id];
  }
  await writeFile(STATE_PATH, JSON.stringify(state, null, 2));
}

// -- Load Sources ------------------------------------------------------------

async function loadSources() {
  const sourcesPath = join(SCRIPT_DIR, '..', 'config', 'default-sources.json');
  return JSON.parse(await readFile(sourcesPath, 'utf-8'));
}

// -- YouTube Fetching (Supadata API) -----------------------------------------

async function fetchYouTubeContent(podcasts, apiKey, state, errors) {
  const cutoff = new Date(Date.now() - PODCAST_LOOKBACK_HOURS * 60 * 60 * 1000);
  const allCandidates = [];

  for (const podcast of podcasts) {
    try {
      let videosUrl;
      if (podcast.type === 'youtube_playlist') {
        videosUrl = `${SUPADATA_BASE}/youtube/playlist/videos?id=${podcast.playlistId}`;
      } else {
        videosUrl = `${SUPADATA_BASE}/youtube/channel/videos?id=${podcast.channelHandle}&type=video`;
      }

      const videosRes = await fetch(videosUrl, {
        headers: { 'x-api-key': apiKey }
      });

      if (!videosRes.ok) {
        errors.push(`YouTube: Failed to fetch videos for ${podcast.name}: HTTP ${videosRes.status}`);
        continue;
      }

      const videosData = await videosRes.json();
      const regularIds = videosData.videoIds || videosData.video_ids || [];
      const liveIds = videosData.liveIds || videosData.live_ids || [];
      const videoIds = [...regularIds, ...liveIds];

      console.error(`  ${podcast.name}: found ${regularIds.length} regular + ${liveIds.length} live video IDs`);

      for (const videoId of videoIds.slice(0, 2)) {
        if (state.seenVideos[videoId]) {
          console.error(`    Skipping ${videoId} (already seen)`);
          continue;
        }

        try {
          const metaRes = await fetch(
            `${SUPADATA_BASE}/youtube/video?id=${videoId}`,
            { headers: { 'x-api-key': apiKey } }
          );
          if (!metaRes.ok) {
            console.error(`    Metadata fetch failed for ${videoId}: HTTP ${metaRes.status}`);
            errors.push(`YouTube: Metadata fetch failed for ${videoId}: HTTP ${metaRes.status}`);
            continue;
          }
          const meta = await metaRes.json();
          const publishedAt = meta.uploadDate || meta.publishedAt || meta.date || null;

          console.error(`    Candidate: ${videoId} "${meta.title || 'Untitled'}" published=${publishedAt || 'unknown'}`);
          allCandidates.push({
            podcast, videoId,
            title: meta.title || 'Untitled',
            publishedAt
          });
          await new Promise(r => setTimeout(r, 300));
        } catch (err) {
          errors.push(`YouTube: Error fetching metadata for ${videoId}: ${err.message}`);
        }
      }
    } catch (err) {
      errors.push(`YouTube: Error processing ${podcast.name}: ${err.message}`);
    }
  }

  console.error(`  Total candidates: ${allCandidates.length}, cutoff: ${cutoff.toISOString()}`);

  const withinWindow = allCandidates
    .filter(v => !v.publishedAt || new Date(v.publishedAt) >= cutoff)
    .sort((a, b) => {
      if (a.publishedAt && b.publishedAt) return new Date(a.publishedAt) - new Date(b.publishedAt);
      if (a.publishedAt) return -1;
      if (b.publishedAt) return 1;
      return 0;
    });

  console.error(`  Within window: ${withinWindow.length} video(s)`);
  for (const v of withinWindow) {
    console.error(`    - ${v.videoId} "${v.title}" published=${v.publishedAt || 'unknown'}`);
  }

  const selected = withinWindow[0];
  if (!selected) return [];

  try {
    const videoUrl = `https://www.youtube.com/watch?v=${selected.videoId}`;
    const transcriptRes = await fetch(
      `${SUPADATA_BASE}/youtube/transcript?url=${encodeURIComponent(videoUrl)}&text=true`,
      { headers: { 'x-api-key': apiKey } }
    );

    if (!transcriptRes.ok) {
      errors.push(`YouTube: Failed to get transcript for ${selected.videoId}: HTTP ${transcriptRes.status}`);
      return [];
    }

    const transcriptData = await transcriptRes.json();
    state.seenVideos[selected.videoId] = Date.now();

    return [{
      source: 'podcast',
      name: selected.podcast.name,
      title: selected.title,
      videoId: selected.videoId,
      url: `https://youtube.com/watch?v=${selected.videoId}`,
      publishedAt: selected.publishedAt,
      transcript: transcriptData.content || ''
    }];
  } catch (err) {
    errors.push(`YouTube: Error fetching transcript for ${selected.videoId}: ${err.message}`);
    return [];
  }
}

// -- X/Twitter Fetching (Official API v2) ------------------------------------

async function fetchXContent(xAccounts, bearerToken, state, errors) {
  const results = [];
  const cutoff = new Date(Date.now() - TWEET_LOOKBACK_HOURS * 60 * 60 * 1000);

  const handles = xAccounts.map(a => a.handle);
  let userMap = {};

  for (let i = 0; i < handles.length; i += 100) {
    const batch = handles.slice(i, i + 100);
    try {
      const res = await fetch(
        `${X_API_BASE}/users/by?usernames=${batch.join(',')}&user.fields=name,description`,
        { headers: { 'Authorization': `Bearer ${bearerToken}` } }
      );

      if (!res.ok) {
        errors.push(`X API: User lookup failed: HTTP ${res.status}`);
        continue;
      }

      const data = await res.json();
      for (const user of (data.data || [])) {
        userMap[user.username.toLowerCase()] = {
          id: user.id,
          name: user.name,
          description: user.description || ''
        };
      }
      if (data.errors) {
        for (const err of data.errors) {
          errors.push(`X API: User not found: ${err.value || err.detail}`);
        }
      }
    } catch (err) {
      errors.push(`X API: User lookup error: ${err.message}`);
    }
  }

  for (const account of xAccounts) {
    const userData = userMap[account.handle.toLowerCase()];
    if (!userData) continue;

    try {
      const res = await fetch(
        `${X_API_BASE}/users/${userData.id}/tweets?` +
        `max_results=5` +
        `&tweet.fields=created_at,public_metrics,referenced_tweets,note_tweet` +
        `&exclude=retweets,replies` +
        `&start_time=${cutoff.toISOString()}`,
        { headers: { 'Authorization': `Bearer ${bearerToken}` } }
      );

      if (!res.ok) {
        if (res.status === 429) {
          errors.push(`X API: Rate limited, skipping remaining accounts`);
          break;
        }
        errors.push(`X API: Failed to fetch tweets for @${account.handle}: HTTP ${res.status}`);
        continue;
      }

      const data = await res.json();
      const allTweets = data.data || [];

      const newTweets = [];
      for (const t of allTweets) {
        if (state.seenTweets[t.id]) continue;
        if (newTweets.length >= MAX_TWEETS_PER_USER) break;

        newTweets.push({
          id: t.id,
          text: t.note_tweet?.text || t.text,
          createdAt: t.created_at,
          url: `https://x.com/${account.handle}/status/${t.id}`,
          likes: t.public_metrics?.like_count || 0,
          retweets: t.public_metrics?.retweet_count || 0,
          replies: t.public_metrics?.reply_count || 0,
          isQuote: t.referenced_tweets?.some(r => r.type === 'quoted') || false,
          quotedTweetId: t.referenced_tweets?.find(r => r.type === 'quoted')?.id || null
        });

        state.seenTweets[t.id] = Date.now();
      }

      if (newTweets.length === 0) continue;

      results.push({
        source: 'x',
        name: account.name,
        handle: account.handle,
        bio: userData.description,
        tweets: newTweets
      });

      await new Promise(r => setTimeout(r, 200));
    } catch (err) {
      errors.push(`X API: Error fetching @${account.handle}: ${err.message}`);
    }
  }

  return results;
}

// -- Blog Fetching (HTML scraping) -------------------------------------------

function parseBlogIndex(html, blog) {
  const articles = [];
  const seenSlugs = new Set();

  // Generic strategy: extract article links matching the base URL pattern
  const baseUrlPath = new URL(blog.articleBaseUrl).pathname;
  const linkRegex = new RegExp(`href="${baseUrlPath.replace(/\//g, '\\/')}([a-z0-9-]+)"`, 'gi');
  let linkMatch;
  while ((linkMatch = linkRegex.exec(html)) !== null) {
    const slug = linkMatch[1];
    if (seenSlugs.has(slug)) continue;
    seenSlugs.add(slug);
    articles.push({
      title: '',
      url: `${blog.articleBaseUrl}${slug}`,
      publishedAt: null,
      description: ''
    });
  }
  return articles;
}

function extractArticleContent(html) {
  let title = '';
  let author = '';
  let publishedAt = null;
  let content = '';

  // Try JSON-LD structured data
  const jsonLdRegex = /<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  let jsonLdMatch;
  while ((jsonLdMatch = jsonLdRegex.exec(html)) !== null) {
    try {
      const ld = JSON.parse(jsonLdMatch[1]);
      if (ld['@type'] === 'BlogPosting' || ld['@type'] === 'Article' || ld['@type'] === 'NewsArticle') {
        title = ld.headline || ld.name || '';
        author = ld.author?.name || '';
        publishedAt = ld.datePublished || null;
        break;
      }
    } catch {
      // Not valid JSON-LD, skip
    }
  }

  // Try <h1> for title
  if (!title) {
    const h1Match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
    if (h1Match) title = h1Match[1].replace(/<[^>]+>/g, '').trim();
  }

  // Extract body text
  const articleMatch = html.match(/<article[^>]*>([\s\S]*?)<\/article>/i);
  const bodyHtml = articleMatch ? articleMatch[1] : html;

  content = bodyHtml
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<nav[\s\S]*?<\/nav>/gi, '')
    .replace(/<footer[\s\S]*?<\/footer>/gi, '')
    .replace(/<header[\s\S]*?<\/header>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  return { title, author, publishedAt, content };
}

async function fetchBlogContent(blogs, state, errors) {
  const results = [];
  const cutoff = new Date(Date.now() - BLOG_LOOKBACK_HOURS * 60 * 60 * 1000);

  for (const blog of blogs) {
    console.error(`  Processing blog: ${blog.name}...`);
    let candidates = [];

    try {
      const indexRes = await fetch(blog.indexUrl, {
        headers: { 'User-Agent': 'FollowTraders/1.0 (feed aggregator)' }
      });
      if (!indexRes.ok) {
        errors.push(`Blog: Failed to fetch index for ${blog.name}: HTTP ${indexRes.status}`);
        continue;
      }
      const indexHtml = await indexRes.text();
      candidates = parseBlogIndex(indexHtml, blog);

      const MAX_INDEX_SCAN = MAX_ARTICLES_PER_BLOG;
      const newArticles = [];
      for (const article of candidates.slice(0, MAX_INDEX_SCAN)) {
        if (state.seenArticles[article.url]) continue;
        if (article.publishedAt && new Date(article.publishedAt) < cutoff) continue;
        newArticles.push(article);
        if (newArticles.length >= MAX_ARTICLES_PER_BLOG) break;
      }

      if (newArticles.length === 0) {
        console.error(`    No new articles found`);
        continue;
      }

      console.error(`    Found ${newArticles.length} new article(s), fetching content...`);

      for (const article of newArticles) {
        try {
          const articleRes = await fetch(article.url, {
            headers: { 'User-Agent': 'FollowTraders/1.0 (feed aggregator)' }
          });
          if (!articleRes.ok) {
            errors.push(`Blog: Failed to fetch article ${article.url}: HTTP ${articleRes.status}`);
            continue;
          }
          const articleHtml = await articleRes.text();
          const extracted = extractArticleContent(articleHtml);

          if (!extracted || !extracted.content) {
            errors.push(`Blog: No content extracted from ${article.url}`);
            continue;
          }

          results.push({
            source: 'blog',
            name: blog.name,
            title: extracted.title || article.title || 'Untitled',
            url: article.url,
            publishedAt: extracted.publishedAt || article.publishedAt || null,
            author: extracted.author || '',
            description: article.description || '',
            content: extracted.content
          });

          state.seenArticles[article.url] = Date.now();
          await new Promise(r => setTimeout(r, 500));
        } catch (err) {
          errors.push(`Blog: Error fetching article ${article.url}: ${err.message}`);
        }
      }
    } catch (err) {
      errors.push(`Blog: Error processing ${blog.name}: ${err.message}`);
    }
  }

  return results;
}

// -- Main --------------------------------------------------------------------

async function main() {
  const args = process.argv.slice(2);
  const tweetsOnly = args.includes('--tweets-only');
  const podcastsOnly = args.includes('--podcasts-only');
  const blogsOnly = args.includes('--blogs-only');

  const runTweets = tweetsOnly || (!podcastsOnly && !blogsOnly);
  const runPodcasts = podcastsOnly || (!tweetsOnly && !blogsOnly);
  const runBlogs = blogsOnly || (!tweetsOnly && !podcastsOnly);

  const xBearerToken = process.env.X_BEARER_TOKEN;
  const supadataKey = process.env.SUPADATA_API_KEY;

  if (runPodcasts && !supadataKey) {
    console.error('SUPADATA_API_KEY not set');
    process.exit(1);
  }
  if (runTweets && !xBearerToken) {
    console.error('X_BEARER_TOKEN not set');
    process.exit(1);
  }

  const sources = await loadSources();
  const state = await loadState();
  const errors = [];

  // Fetch tweets
  if (runTweets) {
    console.error('Fetching X/Twitter content...');
    const xContent = await fetchXContent(sources.x_accounts, xBearerToken, state, errors);
    console.error(`  Found ${xContent.length} traders with new tweets`);

    const totalTweets = xContent.reduce((sum, a) => sum + a.tweets.length, 0);
    const xFeed = {
      generatedAt: new Date().toISOString(),
      lookbackHours: TWEET_LOOKBACK_HOURS,
      x: xContent,
      stats: { xTraders: xContent.length, totalTweets },
      errors: errors.filter(e => e.startsWith('X API')).length > 0
        ? errors.filter(e => e.startsWith('X API')) : undefined
    };
    await writeFile(join(SCRIPT_DIR, '..', 'feed-x.json'), JSON.stringify(xFeed, null, 2));
    console.error(`  feed-x.json: ${xContent.length} traders, ${totalTweets} tweets`);
  }

  // Fetch podcasts
  if (runPodcasts) {
    console.error('Fetching YouTube content...');
    const podcasts = await fetchYouTubeContent(sources.podcasts, supadataKey, state, errors);
    console.error(`  Found ${podcasts.length} new episodes`);

    const podcastFeed = {
      generatedAt: new Date().toISOString(),
      lookbackHours: PODCAST_LOOKBACK_HOURS,
      podcasts,
      stats: { podcastEpisodes: podcasts.length },
      errors: errors.filter(e => e.startsWith('YouTube')).length > 0
        ? errors.filter(e => e.startsWith('YouTube')) : undefined
    };
    await writeFile(join(SCRIPT_DIR, '..', 'feed-podcasts.json'), JSON.stringify(podcastFeed, null, 2));
    console.error(`  feed-podcasts.json: ${podcasts.length} episodes`);
  }

  // Fetch blog posts
  if (runBlogs && sources.blogs && sources.blogs.length > 0) {
    console.error('Fetching blog content...');
    const blogContent = await fetchBlogContent(sources.blogs, state, errors);
    console.error(`  Found ${blogContent.length} new blog post(s)`);

    const blogFeed = {
      generatedAt: new Date().toISOString(),
      lookbackHours: BLOG_LOOKBACK_HOURS,
      blogs: blogContent,
      stats: { blogPosts: blogContent.length },
      errors: errors.filter(e => e.startsWith('Blog')).length > 0
        ? errors.filter(e => e.startsWith('Blog')) : undefined
    };
    await writeFile(join(SCRIPT_DIR, '..', 'feed-blogs.json'), JSON.stringify(blogFeed, null, 2));
    console.error(`  feed-blogs.json: ${blogContent.length} posts`);
  }

  await saveState(state);

  if (errors.length > 0) {
    console.error(`  ${errors.length} non-fatal errors`);
  }
}

main().catch(err => {
  console.error('Feed generation failed:', err.message);
  process.exit(1);
});
