import nonebot
from nonebot.adapters.onebot.v12 import Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)


# 在这里加载插件
nonebot.load_builtin_plugins("echo")  # 内置插件
# nonebot.load_plugin("thirdparty_plugin")  # 第三方插件
# nonebot.load_plugins("awesome_bot/plugins")  # 本地插件

if __name__ == "__main__":
    nonebot.run()
