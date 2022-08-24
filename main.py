import ujson
import aiohttp
import asyncio
from pathlib import Path
from loguru import logger
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Optional, Literal, NoReturn, List, Union


class NoticeInfo(TypedDict):
    notice_type: Optional[Literal["bark", "ServerChan"]]
    notice_key: Optional[str]


class UserInfo(BaseModel):
    username: Optional[str]
    password: Optional[str]
    cookie: Optional[str]
    report_type: Literal["inner", "outer"]
    notice_info: Optional[NoticeInfo]


@logger.catch
def load_config(config_path: Optional[Union[Path, str]] = None) -> Optional[List[UserInfo]]:
    if not config_path:
        config_path = Path(__file__).parent / "config.json"
    elif isinstance(config_path, str):
        config_path = Path(config_path)
    if not config_path.is_file():
        raise ValueError(f"读取配置发生错误：未找到{config_path}")
    with open(config_path, "r", encoding="utf-8") as r:
        config = ujson.loads(r.read())
    return [UserInfo(**user) for user in config.get("users")]


class BUAAEpidemicReporter(object):
    login_url: str = "https://app.buaa.edu.cn/uc/wap/login/check"
    get_form_url: str = "https://app.buaa.edu.cn/buaaxsncov/wap/default/get-info"
    inner_post_url: str = "https://app.buaa.edu.cn/buaaxsncov/wap/default/save"
    outer_post_url: str = "https://app.buaa.edu.cn/ncov/wap/default/save"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cookie: Optional[str] = None,
        notice_info: Optional[NoticeInfo] = None,
        report_type: Literal["inner", "outer"] = "inner"
    ):
        if not cookie and (not username or not password):
            raise ValueError("你需要至少给出cookie或者账号密码中的一项作为初始数据！")
        self.username = username
        self.password = password
        self.cookie = cookie
        self.notice_info = notice_info
        self.post_url = self.inner_post_url if report_type == "inner" else self.outer_post_url
        logger.success(f"用户 <{self.username}>：初始化成功，此次填报类型为{'校内' if report_type == 'inner' else '校外'}填报")

    async def get_cookie(self) -> Optional[str]:
        if self.cookie:
            return self.cookie
        logger.info(f"用户 <{self.username}>：正在尝试获取Cookie")
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/101.0.4951.64 Safari/537.36 "
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.login_url, headers=headers, data={"username": self.username, "password": self.password}
            ) as resp:
                data = await resp.json(content_type=resp.headers.get("Content-Type").split(";")[0] or "text/html")
                if data.get("e") != 0:
                    return logger.error(f"用户 <{self.username}>：获取Cookie失败：{data.get('m')}")
                self.cookie = resp.headers["Set-Cookie"]
                logger.success(f"用户 <{self.username}>：Cookie获取成功！")
                return self.cookie

    @logger.catch
    async def get_old_form(self) -> Optional[dict]:
        cookie = await self.get_cookie()
        if not cookie:
            return
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                          "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "Host": "app.buaa.edu.cn",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://app.buaa.edu.cn/site/buaaStudentNcov/index",
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": cookie
        }

        logger.info(f"用户 <{self.username}>：正在尝试获取历史表单")
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.get(self.get_form_url, headers=headers) as resp:
                data = await resp.json(content_type=resp.headers.get("Content-Type").split(";")[0] or "text/html")
        if data.get("e") != 0:
            logger.error(f"用户 <{self.username}>：{data.get('d')}")
            return await self.notice(data.get("d"))
        if not data["d"]["oldInfo"] and not data["d"]["info"]:
            logger.error(f"用户 <{self.username}>：无法获取历史数据！请手动打卡后再试!")
            return await self.notice("无法获取历史数据！请手动打卡后再试!")
        data = data["d"]["oldInfo"] or data["d"]["info"]
        if not data.get("geo_api_info"):
            logger.error(f"用户 <{self.username}>：昨天的信息不完整！请手动填报一天后继续使用本脚本")
            return await self.notice("昨天的信息不完整！请手动填报一天后继续使用本脚本")
        logger.success(f"用户 <{self.username}>：获取历史表单成功！")
        logger.info(f"用户 <{self.username}>：正在生成新表单")
        geo_info = ujson.loads(data.get("geo_api_info"))
        address_component = geo_info["addressComponent"]
        province = address_component["province"]
        city = province if province in {"北京市", "上海市", "重庆市", "天津市"} else address_component["city"]
        area = address_component["province"] + " " + address_component["city"] + " " + address_component["district"]
        address = geo_info["formattedAddress"]
        data["province"] = province
        data["city"] = city
        data["area"] = area
        data["address"] = address
        data["ismoved"] = "0"
        data["bztcyy"] = ""
        data["sfsfbh"] = "0"
        logger.success(f"用户 <{self.username}>：新表单生成完毕")

        return data

    @logger.catch
    async def report(self) -> NoReturn:
        cookie = await self.get_cookie()
        form = await self.get_old_form()
        if not cookie or not form:
            return
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                          "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "Host": "app.buaa.edu.cn",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-cn",
            "Connection": "keep-alive",
            "Referer": "https://app.buaa.edu.cn/site/buaaStudentNcov/index",
            'Content-Type': 'application/x-www-form-urlencoded',
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": cookie
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.post_url, headers=headers, data=form) as resp:
                res = await resp.json(content_type=resp.headers.get("Content-Type").split(";")[0] or "text/html")
                if res.get("e") != 0:
                    logger.error(f"用户 <{self.username}>：打卡发生错误：" + res.get("m"))
                    await self.notice("打卡发生错误：" + res.get("m"))
                else:
                    logger.success(f"用户 <{self.username}>：打卡成功！")
                    await self.notice()

    async def notice(self, error: Optional[str] = None) -> NoReturn:
        if not self.notice_info:
            return logger.info(f"用户 <{self.username}>：未查找到notice_info")
        elif not self.notice_info["notice_type"] or not self.notice_info["notice_key"]:
            return logger.error(f"用户 <{self.username}>：notice_info数据填写不全！")
        notice_type = self.notice_info["notice_type"]
        notice_key = self.notice_info["notice_key"]
        message = error or "打卡成功！"
        status = "本次打卡成功" if not error else "本次打卡发生错误，详情请点击查看"
        if notice_type.lower() == "serverchan":
            url = f"https://sctapi.ftqq.com/{notice_key}.send?title=用户<{self.username}>{status}&desp={message}"
        elif notice_type.lower() == "bark":
            url = f"https://api.day.app/{notice_key}/用户<{self.username}>打卡通知：{message}"
        else:
            return logger.error(f"用户 <{self.username}>：未知/不支持的notice_type：{notice_type}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as _:
                pass


async def run():
    users = load_config()
    tasks = [asyncio.create_task(BUAAEpidemicReporter(**user_info.dict()).report()) for user_info in users]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())
