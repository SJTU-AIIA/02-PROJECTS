欢迎来到AI创协开发的项目管理中心！所有同学们开发的项目都将在此仓库中保存，同时为同学们提供了高效的AI向部署工具，希望能帮助到大家找到学习AI的优质资源！

### 其他语言 Other Languages：
[English README.md Version](https://github.com/SJTU-AIIA/02-PROJECTS/blob/main/locales/EN-US/README.md)

# 新手操作指南：

## AIIA-CLI (PROJ-CLI) 用法详解：
### 初始步骤  
安装 AIIA-CLI（共学部开发的项目管理工具）  
```bash  
pip install --upgrade aiia-cli  
```  
进入 `02-PROJECTS` 仓库根目录打开命令行  

### 如已有项目仓库：
```bash  
proj-cli import-repo 仓库URL
```  

### 如需新建项目：
```bash  
proj-cli new 项目名称
```  

### 如需格式化已有项目：
```bash  
proj-cli format 项目名称
```  
*可在此提供默认端口和构建环境变量（端口默认8000:8000，分支默认main，环境变量默认为空）详情查看下方文档*  
*创建项目文件夹后，请稍候片刻后刷新GitHub仓库管理manifest和README文件*  

### 登录GHCR：
运行`proj-cli login`输入个人访问令牌(PAT)，需在GitHub设置 > 开发者设置 > 个人访问令牌中勾选`repo`和`write:packages`/`read:packages`权限，用于GHCR认证  

### 构建与本地部署  
```bash  
cd projects/<你的项目名称>  
proj-cli login  
proj-cli deploy --bump major  # 部署新Docker镜像，主版本升级（其他版本可用major patch参数替代）
proj-cli run  
```  
大功告成！ 

---

## AIIA-CLI (PROJ-CLI) 文档  
### 新建项目  
```bash  
proj-cli new 项目名称 [OPTION] --port 8000:8000 --env 环境变量1=值 --env 环境变量2=值  
```  
*在/projects目录创建项目，指定端口和环境变量（默认8000:8000）*  

### 格式化项目  
```bash  
proj-cli format 项目名称 [OPTION] --port 8000:8000 --env 环境变量1=值 --env 环境变量2=值
```  
*将模板文件注入项目目录，冲突文件提示处理，README.md提供合并选项*  

### 导入外部仓库  
```bash  
proj-cli import-repo 仓库URL [OPTION] --rename 新项目名称 --port 8000:8000 --env 环境变量1=值 --env 环境变量2=值 --branch 分支  
```  
*默认分支main，自动生成规范文件*  

### 提交项目  
```bash  
proj-cli submit "提交信息"  
```  
*需在项目目录内执行，提交并推送变更*  

### 部署Docker镜像  
```bash  
proj-cli deploy [OPTION] --bump major/minor/patch
```  
*需存在Dockerfile，支持语义化版本控制（v1.0.0, v1.0.1等）*  

### 运行容器  
```bash  
proj-cli run [OPTION] --version 版本 --port 端口映射 --env 变量=值
```  
*默认使用最新版本和项目创建时配置*  