def update_holidays():
    import importlib.metadata
    import subprocess
    package_name = "chinesecalendar"
    try_get_version = "0"
    try:
        try_get_version = importlib.metadata.version(package_name)
    except ImportError:
        pass
    package_version = try_get_version

    import requests
    def get_latest_version():
        # 构造查询最新版本的 API URL
        url = f"https://pypi.org/pypi/{package_name}/json"
        # 发送 GET 请求
        response = requests.get(url)
        # 获取响应数据
        data = response.json()
        # 解析响应数据，获取最新版本号
        latest_version = data["info"]["version"]
        return latest_version

    package_last_version = get_latest_version()
    if package_version != package_last_version:
        if package_version == "0":
            subprocess.run(["pip", "install", package_name])
            raise Exception(f"{package_name} 没有安装，应该已经安装完成，请检查后再次运行。")
        else:
            print(f"\033[31m{package_name} 已过期，将更新为 {package_last_version}\033[0m")
            subprocess.run(["pip", "install", "--upgrade", package_name])
            raise Exception(f"{package_name} 版本更新完成，请检查后再次运行。")
