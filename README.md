<h1 align="center" style="border-bottom: none">
  buaa-covid-19-report
</h1>

<p align="center">
  使用 Python 编写的自动填报北航 COVID-19 疫情信息的脚本。
</p>

## 使用方法
- 首先，确保你的 `Python` 版本大于等于 `3.8`
- 使用 `pip` 安装依赖，进入脚本所在文件夹，执行 `pip install -r requirements.txt`
- 进入 `config.json`，填写个人信息，支持多用户，各项含义请看下方 `配置文件`
- 运行脚本 `python main.py`，可配合 `crontab` 等方法实现每日定时打卡

## 配置文件
`config.json` 结构如下：
```json
{
  "users": [
    {
      "username": "",
      "password": "",
      "report_type": "",
      "notice_info": {
        "notice_type": "",
        "notice_key": ""
      }
    }
  ]
}
```
其中，各项含义如下
| 项 | 含义 | 备注 |
| ---- | ---- | ---- |
| username | 同一身份认证账号用户名 |  |
| password | 同一身份认证账号密码 |  |
| report_type | 填报类型 | 分为 `inner` 校内填报和 `outer` 校外填报 |
| notice_info | 打卡通知相关 | 若不需要通知可删除此项或保持原样 |
| notice_info -> notice_type | 通知使用应用 | 目前只支持 `ServerChan` 和 `bark` |
| notice_info -> notice_key | 通知应用Key | 其中 `ServerChan` 为 `SendKey`，`bark` 为 `https://api.day.app/{key}/{content}` 中 `key` 所在位置的值 |

## 多用户打卡
只需将用户信息填入 `config.json` 即可，示例如下：
```json
{
  "users": [
    {
      "username": "user1",
      "password": "pwd1",
      "report_type": "inner",
      "notice_info": {
        "notice_type": "bark",
        "notice_key": "bark_key"
      }
    },
    {
      "username": "user2",
      "password": "pwd2",
      "report_type": "outer",
      "notice_info": {
        "notice_type": "ServerChan",
        "notice_key": "SendKey"
      }
    }
  ]
}
```
