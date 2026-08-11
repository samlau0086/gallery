# Product Gallery

这是一个纯静态商品图库。前端入口为 `index.html`，商品数据保存在 `data/` 目录。项目不依赖 Node.js、数据库或常驻后端服务，生产环境由 Cloudflare Pages 托管。

## 部署架构

发布由 GitHub Actions 自动执行：

1. 将变更推送到 GitHub 仓库的 `main` 分支。
2. GitHub Actions 运行 [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)。
3. 工作流执行 `python merge_data.py`，读取 `data/` 下的全部 JSON 商品文件，并在仓库根目录生成：
   - `data_index.json`：前端加载的分片清单。
   - `all_data_0.json`、`all_data_1.json` 等：每 1,000 条商品一份的数据分片。
4. `cloudflare/pages-action` 将仓库根目录（`directory: '.'`）上传至 Cloudflare Pages 项目 `gallery`。
5. Cloudflare Pages 为该次部署提供站点地址；生产部署对应 `main` 分支。

前端打开后会请求 `./data_index.json`，再按清单加载 `all_data_*.json`。因此 `merge_data.py` 是部署前必须成功执行的一步。

## 首次配置 Cloudflare Pages

以下操作需要拥有对应 Cloudflare 账户和 GitHub 仓库的管理员权限。

### 1. 创建 Cloudflare Pages 项目

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)。
2. 在左侧打开 **Workers & Pages**。
3. 选择 **Create application**，再选择 **Pages**。
4. 选择 **Upload assets**，创建一个 Pages 项目。
5. 项目名称填写 `gallery`，必须与 [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) 中的 `projectName` 保持一致。
6. 可先上传一个任意的临时 HTML 文件以完成项目创建。之后的正式发布全部由 GitHub Actions 覆盖，不需要在 Dashboard 手动上传站点文件。

完成后，Cloudflare 会分配一个形如 `https://gallery.pages.dev` 的默认域名。实际域名可能会因项目名称冲突而不同，以 Cloudflare Dashboard 显示的地址为准。

### 2. 创建 Cloudflare API Token

GitHub Actions 通过 API Token 发布，所以不要使用 Cloudflare 的全局 API Key。

1. 在 Cloudflare Dashboard 右上角打开个人头像，选择 **My Profile**。
2. 打开 **API Tokens**，点击 **Create Token**。
3. 选择适用于 Cloudflare Pages 编辑的模板；如果没有合适模板，选择 **Create Custom Token**。
4. 为 Token 配置权限：
   - `Account` -> `Cloudflare Pages` -> `Edit`
   - 如 Dashboard 要求读取账户信息，再添加 `Account` -> `Account Settings` -> `Read`
5. `Account Resources` 选择当前账户；如可限定资源，优先只授权给承载 `gallery` 的账户。
6. 点击创建并立即复制 Token。它只会完整显示一次，不能提交到仓库或粘贴到公开位置。

### 3. 获取 Cloudflare Account ID

1. 回到 Cloudflare Dashboard 首页。
2. 在右侧的账户信息区域找到 **Account ID** 并复制。
3. 注意：这里需要的是账户级 Account ID，不是 Zone ID，也不是 Pages 项目名称。

### 4. 在 GitHub 仓库配置 Secrets

1. 打开 GitHub 仓库 `samlau0086/gallery`。
2. 依次进入 **Settings** -> **Secrets and variables** -> **Actions**。
3. 点击 **New repository secret**，依次新增以下两个 Secret：

| Secret 名称 | 填写内容 |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | 第 2 步创建的 Cloudflare API Token |
| `CLOUDFLARE_ACCOUNT_ID` | 第 3 步复制的 Cloudflare Account ID |

Secret 名称必须与工作流中的名称完全一致。GitHub 只会在 Actions 执行时注入它们，日志中会被遮蔽。

## 日常发布流程

1. 修改 `index.html`、`data/` 中的数据，或其他需要发布的静态资源。
2. 在本地运行一次构建检查：

   ```powershell
   python merge_data.py
   ```

3. 可用任意静态服务器在仓库根目录预览，例如：

   ```powershell
   python -m http.server 8000
   ```

   然后访问 `http://localhost:8000/`。不要直接双击 `index.html` 作为最终验证方式，因为浏览器可能会限制本地文件协议下的 JSON 请求。

4. 提交并推送到 `main`：

   ```powershell
   git add index.html data .github/workflows/deploy.yml merge_data.py
   git commit -m "update gallery"
   git push origin main
   ```

5. 打开 GitHub 仓库的 **Actions** 页面，进入 **Build and Deploy to Cloudflare Pages**，确认本次运行成功。
6. 在 Cloudflare Dashboard 的 **Workers & Pages** -> `gallery` -> **Deployments** 中确认部署状态和生产地址。

通常 Cloudflare Pages 会在工作流完成后很快更新生产站点；若浏览器仍显示旧资源，使用强制刷新，或等待 CDN 缓存刷新后再确认。

## 自定义域名

若需要使用自己的域名：

1. 在 Cloudflare Dashboard 打开 **Workers & Pages** -> `gallery`。
2. 进入 **Custom domains**，点击 **Set up a domain**。
3. 输入要绑定的域名，例如 `gallery.example.com`。
4. 如果该域名的 DNS 已托管在同一个 Cloudflare 账户，按提示确认即可，Cloudflare 会自动创建或提示创建相应记录。
5. 如果 DNS 不在 Cloudflare，按界面提供的 CNAME 验证或 DNS 记录说明，在域名服务商处完成配置。
6. 等待域名状态显示为 **Active**，再访问域名确认站点正常打开。

HTTPS 证书由 Cloudflare 自动签发和续期。绑定域名后，建议在 Pages 的项目设置中将一个域名设为主域名，并检查站点资源是否全部通过 HTTPS 加载。

## 修改部署配置

部署配置文件是 [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)。常见改动如下：

- **改 Cloudflare 项目名**：修改 `projectName`，并在 Cloudflare 创建同名 Pages 项目。
- **改发布分支**：修改 `on.push.branches`，例如从 `main` 改为 `production`。
- **改发布目录**：当前是 `directory: '.'`。若后续将构建产物放入 `dist/`，应改为 `directory: 'dist'`，并确保数据分片也生成到该目录。
- **调整数据分片大小**：修改 `merge_data.py` 的 `CHUNK_SIZE`。修改后应重新部署，以同步生成新的 `data_index.json` 和 `all_data_*.json`。

## 常见问题

### GitHub Actions 报鉴权或权限错误

检查 GitHub Secrets 是否存在、名称是否完全一致，并确认 API Token 具有当前账户的 `Cloudflare Pages: Edit` 权限。Token 过期、撤销或账号不匹配时，需要在 Cloudflare 重新创建 Token 并更新 GitHub Secret。

### 报错找不到 Cloudflare Pages 项目

确认 Cloudflare 中已经存在 `gallery` 项目，并检查工作流中的 `projectName` 是否一致。项目名通常使用小写字母、数字和连字符最稳妥。

### 部署成功但页面没有商品

先查看 Actions 日志中 `Merge JSON files` 步骤是否成功。然后确认 `data/` 中 JSON 文件是有效 JSON 数组；前端需要 `data_index.json` 和 `all_data_*.json` 这些由脚本生成的文件。

### 页面加载数据时出现 404

工作流当前部署的是仓库根目录，`index.html`、`data_index.json` 和 `all_data_*.json` 必须处在最终上传目录中。不要只部署 `data/` 目录，也不要在修改 `directory` 后忘记同步调整数据生成位置。

### 已推送代码但线上还是旧版本

确认提交已经推送到 `main`，并查看对应 GitHub Actions 是否成功。随后到 Cloudflare Pages 的 Deployments 页面确认最新生产部署的提交版本；最后用无痕窗口或强制刷新排除浏览器缓存。

## 数据维护脚本

- `translate_data.py`：将 `data-original/` 中标题和描述翻译为英文数据。
- `tags_updater.py`：将 `data/` 中的标签从字符串规范化为数组。
- `merge_data.py`：为前端生成部署所需的分片文件和索引；每次数据更新后都会由 GitHub Actions 自动运行。

## 安全注意事项

- 不要将 `CLOUDFLARE_API_TOKEN`、Account ID 的管理后台截图或其他凭据提交到仓库。
- 不要把 API Token 写入 `deploy.yml`、`index.html` 或任何数据 JSON。
- 如果 Token 泄露，立刻在 Cloudflare 的 **API Tokens** 页面撤销它，重新创建 Token，并更新 GitHub Secret。
