# 项目管理面板  
欢迎来到项目管理中心！此处将会跟踪所有项目进展。

### 其他语言 Other Languages：
[English README.md Version](https://github.com/SJTU-AIIA/02-PROJECTS/blob/main/locales/EN-US/README.md)

新手贡献指南请参考下方示例：

## 示例 AIIA-CLI (PROJ-CLI) 工作流  
### 初始步骤  
安装 AIIA-CLI（专有定制开发的项目管理工具）  
```bash  
pip install --upgrade aiia-cli  
```  
进入 `02-PROJECTS` 仓库根目录打开命令行  

### 已有项目仓库  
```bash  
proj-cli import_repo <你的仓库URL> [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值 --branch 分支]  
```  

### 新建项目  
```bash  
proj-cli new 项目名称 [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值]  
```  

### 格式化已有项目  
```bash  
proj-cli format 项目名称 [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值]  
```  
*可在此提供默认端口和构建环境变量（端口默认8000:8000，分支默认main，环境变量默认为空）*  
*创建项目文件夹后，请稍候刷新GitHub仓库管理manifest和README文件*  

**登录提示**：运行`proj-cli login`输入个人访问令牌(PAT)，需在GitHub设置 > 开发者设置 > 个人访问令牌中勾选`repo`和`write:packages`/`read:packages`权限，用于GHCR认证  

### 构建与部署  
```bash  
cd projects/<你的项目名称>  
proj-cli login  
proj-cli deploy --bump major  # 部署新Docker镜像，主版本升级  
proj-cli run  
```  
大功告成！测试您的新项目！  

---

## AIIA-CLI (PROJ-CLI) 文档  
### 新建项目  
```bash  
proj-cli new 项目名称 [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值]  
```  
*在/projects目录创建项目，指定端口和环境变量（默认8000:8000）*  

### 格式化项目  
```bash  
proj-cli format 项目名称 [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值]  
```  
*将模板文件注入项目目录，冲突文件提示处理，README.md提供合并选项*  

### 导入外部仓库  
```bash  
proj-cli import_repo 仓库URL [--port 8000:8000 --env 环境变量1=值 --env 环境变量2=值 --branch 分支]  
```  
*默认分支main，自动生成规范文件*  

### 提交项目  
```bash  
proj-cli submit "提交信息"  
```  
*需在项目目录内执行，提交并推送变更*  

### 部署Docker镜像  
```bash  
proj-cli deploy [--bump major/minor/patch]  
```  
*需存在Dockerfile，支持语义化版本控制*  

### 运行容器  
```bash  
proj-cli run [--version 版本 --port 端口映射 --env 变量=值]  
```  
*默认使用最新版本和项目创建时配置*  

---

## 手动操作指南  
### 1. 复制模板  
```bash  
cp -r projects/.template projects/我的项目  
```  
### 2. 编辑manifest.json  
```json  
{
  "name": "我的项目",
  "authors": ["@张三", "@李四"],
  "created": "2023-08-25T09:30:00+08:00", 
  "license": "MIT",
  "tags": ["大模型", "对话系统"]
}  
```  
### 3. 提交变更  
```bash  
git checkout -b 我的项目  
git add projects/我的项目  
git commit -m "新增我的项目"  
git push origin 我的项目  
```  

*注：所有命令行参数保持英文格式，中文仅作说明使用*  
*建议优先使用CLI工具保证配置规范性*