import inspect
import time
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, NamedTuple, no_type_check, Union, Dict, Any, TypeVar, Tuple

from pydantic import BaseModel

__all__ = ["root_path", "data_path", "BaseModelWithSetter", "BaseModelWithUpdate", "GameRecord", "GameInfo",
           "MmtData",
           "Award", "GameSignInfo", "MissionData", "MissionState", "GenshinNote", "StarRailNote", "ZzzNote",
           "GenshinNoteNotice",
           "StarRailNoteNotice", "ZzzNoteNotice", "BaseApiStatus", "CreateMobileCaptchaStatus", "GetCookieStatus",
           "MissionStatus", "GetFpStatus", "BoardStatus", "GenshinNoteStatus", "StarRailNoteStatus",
           "ZzzNoteStatus",
           "QueryGameTokenQrCodeStatus", "GeetestResult", "GeetestResultV4", "CommandUsage"]

root_path = Path(__name__).parent.absolute()
'''NoneBot2 机器人根目录'''

data_path = root_path / "data" / "nonebot-plugin-mystool"
'''插件数据保存目录'''


class BaseModelWithSetter(BaseModel):
    """
    可以使用@property.setter的BaseModel

    目前pydantic 1.10.7 无法使用@property.setter
    issue: https://github.com/pydantic/pydantic/issues/1577#issuecomment-790506164
    """

    @no_type_check
    def __setattr__(self, name, value):
        try:
            super().__setattr__(name, value)
        except ValueError as e:
            setters = inspect.getmembers(
                self.__class__,
                predicate=lambda x: isinstance(x, property) and x.fset is not None
            )
            for setter_name, func in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    break
            else:
                raise e


class BaseModelWithUpdate(BaseModel):
    """
    可以使用update方法的BaseModel
    """
    _T = TypeVar("_T", bound=BaseModel)

    @abstractmethod
    def update(self, obj: Union[_T, Dict[str, Any]]) -> _T:
        """
        更新数据对象

        :param obj: 新的数据对象或属性字典
        :raise TypeError
        """
        if isinstance(obj, type(self)):
            obj = obj.dict()
        items = filter(lambda x: x[0] in self.__fields__, obj.items())
        for k, v in items:
            setattr(self, k, v)
        return self


class GameRecord(BaseModel):
    """
    用户游戏数据
    """
    region_name: str
    """服务器区名"""

    game_id: int
    """游戏ID"""

    level: int
    """用户游戏等级"""

    region: str
    """服务器区号"""

    game_role_id: str
    """用户游戏UID"""

    nickname: str
    """用户游戏昵称"""


class GameInfo(BaseModel):
    """
    游戏信息数据
    """
    # ABBR_TO_ID: Dict[int, Tuple[str, str]] = {}
    # '''
    # 游戏ID(game_id)与缩写和全称的对应关系
    # >>> {游戏ID, (缩写, 全称)}
    # '''
    id: int
    """游戏ID"""

    app_icon: str
    """游戏App图标链接(大)"""

    op_name: str
    """游戏代号(英文数字, 例如hk4e)"""

    en_name: str
    """游戏代号2(英文数字, 例如ys)"""

    icon: str
    """游戏图标链接(圆形, 小)"""

    name: str
    """游戏名称"""


class MmtData(BaseModel):
    """
    短信验证码-人机验证任务申请-返回数据
    """
    challenge: Optional[str]
    gt: Optional[str]
    """验证ID，即 极验文档 中的captchaId，极验后台申请得到"""
    mmt_key: Optional[str]
    """验证任务"""
    new_captcha: Optional[bool]
    """宕机情况下使用"""
    risk_type: Optional[str]
    """结合风控融合，指定验证形式"""
    success: Optional[int]
    use_v4: Optional[bool]
    """是否使用极验第四代 GT4"""


class Award(BaseModel):
    """
    签到奖励数据
    """
    name: str
    """签到获得的物品名称"""
    icon: str
    """物品图片链接"""
    cnt: int
    """物品数量"""


class GameSignInfo(BaseModel):
    is_sign: bool
    """今日是否已经签到"""
    total_sign_day: int
    """已签多少天"""
    sign_cnt_missed: int
    """漏签多少天"""


class MissionData(BaseModel):
    points: int
    """任务米游币奖励"""
    name: str
    """任务名字，如 讨论区签到"""
    mission_key: str
    """任务代号，如 continuous_sign"""
    threshold: int
    """任务完成的最多次数"""


class MissionState(BaseModel):
    current_myb: int
    """用户当前米游币数量"""
    state_dict: Dict[str, Tuple[MissionData, int]]
    """所有任务对应的完成进度 {mission_key, (MissionData, 当前进度)}"""


class GenshinNote(BaseModel):
    """
    原神实时便签数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_resin: Optional[int]
    """当前树脂数量"""
    finished_task_num: Optional[int]
    """每日委托完成数"""
    current_expedition_num: Optional[int]
    """探索派遣 进行中的数量"""
    max_expedition_num: Optional[int]
    """探索派遣 最多派遣数"""
    current_home_coin: Optional[int]
    """洞天财瓮 未收取的宝钱数"""
    max_home_coin: Optional[int]
    """洞天财瓮 最多可容纳宝钱数"""
    transformer: Optional[Dict[str, Any]]
    """参量质变仪相关数据"""
    resin_recovery_time: Optional[int]
    """剩余树脂恢复时间"""

    @property
    def transformer_text(self):
        """
        参量质变仪状态文本
        """
        try:
            if not self.transformer['obtained']:
                return '未获得'
            elif self.transformer['recovery_time']['reached']:
                return '已准备就绪'
            else:
                return f"{self.transformer['recovery_time']['Day']} 天" \
                       f"{self.transformer['recovery_time']['Hour']} 小时 " \
                       f"{self.transformer['recovery_time']['Minute']} 分钟"
        except KeyError:
            return None

    @property
    def resin_recovery_text(self):
        """
        剩余树脂恢复文本
        """
        try:
            if not self.resin_recovery_time:
                return ':未获得时间数据'
            elif self.resin_recovery_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.resin_recovery_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None


class StarRailNote(BaseModel):
    """
    崩铁实时便签数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_stamina: Optional[int]
    """当前开拓力"""
    max_stamina: Optional[int]
    """最大开拓力"""
    stamina_recover_time: Optional[int]
    """剩余体力恢复时间"""
    current_train_score: Optional[int]
    """当前每日实训值"""
    max_train_score: Optional[int]
    """最大每日实训值"""
    current_rogue_score: Optional[int]
    """当前模拟宇宙积分"""
    max_rogue_score: Optional[int]
    """最大模拟宇宙积分"""
    accepted_expedition_num: Optional[int]
    """已接受委托数量"""
    total_expedition_num: Optional[int]
    """最大委托数量"""
    has_signed: Optional[bool]
    """当天是否签到"""

    @property
    def stamina_recover_text(self):
        """
        剩余体力恢复文本
        """
        try:
            if not self.stamina_recover_time:
                return ':未获得时间数据'
            elif self.stamina_recover_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.stamina_recover_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None


class ZzzNote(BaseModel):
    """
    绝区零实时便签数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_energy: Optional[int]
    """当前电量"""
    max_energy: Optional[int]
    """最大电量"""
    restore: Optional[int]
    """剩余恢复时间"""
    max_vitality: Optional[int]
    """最大每日活力"""
    current_vitality: Optional[int]
    """当前每日活力"""
    sale_state: Optional[str]
    """经营状态"""
    card_sign: Optional[str]
    """刮刮卡"""
    has_signed: Optional[bool]
    """当天是否签到"""

    @property
    def restore_recover_text(self):
        """
        剩余体力恢复文本
        """
        try:
            if self.restore == 0:
                return "已全部恢复"
            # 计算小时数
            hours = self.restore // 3600
            # 计算剩余秒数，并从中得出分钟数
            remaining_seconds_after_hours = self.restore % 3600
            minutes = remaining_seconds_after_hours // 60
            # 计算最终剩余的秒数
            seconds = remaining_seconds_after_hours % 60
            return f"{hours}小时{minutes}分钟{seconds}秒"
        except KeyError:
            return None


class GenshinNoteNotice(GenshinNote):
    """
    原神便签通知状态
    """
    current_resin: bool = False
    """是否达到阈值"""
    current_resin_full: bool = False
    """是否溢出"""
    current_home_coin: bool = False
    transformer: bool = False


class StarRailNoteNotice(StarRailNote):
    """
    星穹铁道便签通知状态
    """
    current_stamina: bool = False
    """是否达到阈值"""
    current_stamina_full: bool = False
    """是否溢出"""
    current_train_score: bool = False
    current_rogue_score: bool = False


class ZzzNoteNotice(ZzzNote):
    """
    绝区零便签通知状态
    """
    current_energy: bool = False
    """是否达到阈值"""
    current_energy_full: bool = False
    """是否溢出"""


class BaseApiStatus(BaseModel):
    """
    API返回结果基类
    """
    success = False
    """成功"""
    network_error = False
    """连接失败"""
    incorrect_return = False
    """服务器返回数据不正确"""
    login_expired = False
    """登录失效"""
    need_verify = False
    """需要进行人机验证"""
    invalid_ds = False
    """Headers DS无效"""

    def __bool__(self):
        return self.success

    @property
    def error_type(self):
        """
        返回错误类型
        """
        for key, field in self.__fields__.items():
            if field and key != "success":
                return key
        return None


class CreateMobileCaptchaStatus(BaseApiStatus):
    """
    发送短信验证码 返回结果
    """
    incorrect_geetest = False
    """人机验证结果数据无效"""
    not_registered = False
    """手机号码未注册"""
    invalid_phone_number = False
    """手机号码无效"""
    too_many_requests = False
    """发送过于频繁"""


class GetCookieStatus(BaseApiStatus):
    """
    获取Cookie 返回结果
    """
    incorrect_captcha = False
    """验证码错误"""
    missing_login_ticket = False
    """Cookies 缺少 login_ticket"""
    missing_bbs_uid = False
    """Cookies 缺少 bbs_uid (stuid, ltuid, ...)"""
    missing_cookie_token = False
    """Cookies 缺少 cookie_token"""
    missing_stoken = False
    """Cookies 缺少 stoken"""
    missing_stoken_v1 = False
    """Cookies 缺少 stoken_v1"""
    missing_stoken_v2 = False
    """Cookies 缺少 stoken_v2"""
    missing_mid = False
    """Cookies 缺少 mid"""


class MissionStatus(BaseApiStatus):
    """
    米游币任务 返回结果
    """
    failed_getting_post = False
    """获取文章失败"""
    already_signed = False
    """已经完成过签到"""


class GetFpStatus(BaseApiStatus):
    """
    兑换操作 返回结果
    """
    invalid_arguments = False
    """参数错误"""


class BoardStatus(BaseApiStatus):
    """
    实时便签 返回结果
    """
    game_record_failed = False
    """获取用户游戏数据失败"""
    game_list_failed = False
    """获取游戏列表失败"""


class GenshinNoteStatus(BoardStatus):
    """
    原神实时便签 返回结果
    """
    no_genshin_account = False
    """用户没有任何原神账户"""


class StarRailNoteStatus(BoardStatus):
    """
    星铁实时便签 返回结果
    """
    no_starrail_account = False
    """用户没有任何星铁账户"""


class ZzzNoteStatus(BoardStatus):
    """
    绝区零实时便签 返回结果
    """
    no_zzz_account = False
    """用户没有任何绝区零账户"""


class QueryGameTokenQrCodeStatus(BaseApiStatus):
    """
    星铁实时便签 返回结果
    """
    qrcode_expired = False
    """二维码已过期"""
    qrcode_init = False
    """二维码未扫描"""
    qrcode_scanned = False
    """二维码已扫描但未确认"""


GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)
"""人机验证结果数据"""


class GeetestResultV4(BaseModel):
    """
    GEETEST GT4 人机验证结果数据
    """
    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str


class CommandUsage(BaseModel):
    """
    插件命令用法信息
    """
    name: Optional[str]
    description: Optional[str]
    usage: Optional[str]
