# DOTA Auto Eval 管理系统前端

这是DOTA Auto Eval项目的管理系统前端部分。该系统使用现代化的Vue 3技术栈构建，提供了直观的用户界面来管理和监控DOTA自动评估系统。

## 技术栈

- Vue 3 - 渐进式JavaScript框架
- Vite - 下一代前端构建工具
- Element Plus - 基于Vue 3的组件库
- ECharts - 强大的数据可视化图表库
- Vue Router - Vue.js官方路由管理器

## 系统要求

- Node.js 16.0.0 或更高版本
- npm 7.0.0 或更高版本

## 开始使用

### 1. 安装依赖

```bash
npm install
```

### 2. 开发环境运行

```bash
npm run dev
```

启动后，访问 `http://localhost:5173` 即可看到开发环境的应用。

### 3. 生产环境构建

```bash
npm run build
```

构建完成后，生成的文件将位于 `dist` 目录中。

### 4. 预览生产构建

```bash
npm run preview
```

## 推荐的IDE设置

推荐使用 [VSCode](https://code.visualstudio.com/) 进行开发，并安装以下插件：

- [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) - Vue 3的官方IDE支持
- [Vue Devtools](https://devtools.vuejs.org/) - Vue.js开发调试工具

注意：如果已安装Vetur插件，请在使用Vue 3项目时禁用它。

## 项目结构

```
manage_frontend/
├── dist/           # 构建输出目录
├── public/         # 静态资源目录
├── src/           # 源代码目录
├── .vscode/       # VSCode配置文件
├── index.html     # 入口HTML文件
├── vite.config.js # Vite配置文件
└── package.json   # 项目配置文件
```

## 自定义配置

如需自定义构建配置，请参考 [Vite配置文档](https://vitejs.dev/config/)。

## 注意事项

- 本项目使用 `patch-package` 进行依赖包补丁管理
- 确保在开发时遵循Vue 3的组合式API最佳实践
- 使用Element Plus组件库时，建议按需导入以优化打包体积
