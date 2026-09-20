# 课程部署架构总结（T-0920-62，Claire）

*课程发售（09-25 定）的后端基础设施。本文档记录技术实现路线，不含课程内容。*

## 架构设计

课程通过 **Cloudflare Pages + Whop API** 二层实现：

| 层 | 技术 | 职责 |
|---|---|---|
| 静态资产 | Cloudflare Pages（CF Functions） | 路由、部署、全球分发 |
| 会员校验 | Whop SDK（Pages Functions 中间件） | JWT 签名验证、访问权限检查 |
| 交付方式 | iframe 嵌入（whop.com 内）| 浏览器 sandbox 隔离、三方 localStorage 兼容 |

## 当前状态（09-20 完成）

### ✅ 已就位
- **部署包**：94 个静态文件、5.4 MB，路径兼容相对导入、无绝对路径依赖
- **Whop App 壳**：权限校验双层（JWT 本地验签 + 远程访问检查），单测 5/5 通过
- **本地验证**：课件渲染、交互、响应式布局均已测试并截图存档
- **iframe 兼容**：CSP/X-Frame-Options/localStorage 跨域场景自检完成，无阻塞点

### ⏳ 待 Andy 行动（T-0920-61）
1. Cloudflare 账户开设 + Pages 项目建立（10 分钟）
2. Whop 后台 app 注册、获取凭据（15 分钟）
3. 真实环境验证、生产部署（20 分钟）

## 技术判据

**单测覆盖**：权限校验分支逻辑完全覆盖
- ✅ 无 token → 拒绝
- ✅ 有 token 但无权限 → 返回无权限页
- ✅ 有 token 且有权限 → 转发课件
- ✅API 故障处理（返回错误，不当成无权限）
- ✅ 路由缺失处理

**兼容性验证**：三方 iframe 场景
- ✅ 同源 localStorage（数据持久化）
- ✅ 跨域 window 对象访问（无 SecurityError）
- ✅ CSP 宽松（无限制性响应头）

**安全考量**：
- `_headers` 配置 `frame-ancestors https://whop.com`（防点击劫持）
- `_middleware.js` 拦截直接访问、只暴露 `/experiences/*` 路由（防绕过）
- 环境变量占位（不硬编凭据）

## 备注

- 该架构不假设 Whop 的具体实现细节（如头注入行为、token 签名算法），仅使用官方公开文档
- 课件本体（静态资产）无需修改；架构决策仅影响部署和访问层
