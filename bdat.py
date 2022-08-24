#!/usr/bin/python3
#
# Parse tables from Xenoblade BDAT files into per-table HTML files.
# Works with BDATs from Xenoblade 2 or later (Xenoblade X should also work
# if support for big-endian data is added).
#
# Requires Python 3.6 or later.
#
# Public domain, share and enjoy.
#

import argparse
import enum
import os
import re
import struct
import sys


########################################################################
# Utility functions

def u16(data, offset): return struct.unpack('<H', data[offset:offset+2])[0]
def u32(data, offset): return struct.unpack('<I', data[offset:offset+4])[0]

def islistlike(x):
    """Return whether x is a list-like type (list or tuple)."""
    return isinstance(x, list) or isinstance(x, tuple)


########################################################################
# Mapping from hashed strings to their original values

hashes = {
    0x00000000: "",

    # List of tables from program initialization (in init array order):
    # (note that all of these "gimmick*" tables are empty, reason unknown)
    0x1D9A5B2B: None,
    0x22556A12: "gimmickEnemyAff",
    0x33975AC6: "gimmickMob",
    0x5D8D6C4E: "gimmickFixedMob",
    0x8C6F24AC: "gimmickLocation",
    0x8123BF12: "gimmickSchedule",
    0xE6CEEFD4: "gimmickTreasureBox",
    0x722F6DD4: "gimmickMapJump",
    0xE591CF96: "gimmickCollection",
    0xD01AC65F: "gimmickFieldLock",
    0xCA425EC1: "gimmickEnemyPop",
    0x03D42B92: "gimmickElevator",
    0x256CD187: "gimmickElevatorSwitch",
    0x749EF690: "gimmickElevatorCallSwitch",
    0xE74597F5: "gimmickElevatorDoor",
    0x5198B9D5: "gimmickDoor",
    0xBC40F69E: "gimmickEvent",
    0x86B081D1: "gimmickPrecious",
    0x16ED5C1E: "gimmickObject",
    0xBA1BE15F: None,
    0x0EF1103E: "gimmickEnemyWave",
    0xA4253BCA: "gimmickGrave",
    0xCEAA3005: "gimmickFootPrint",
    0x03397BD7: "gimmickWeather",
    0xF941E5C0: "gimmickEtherPoint",
    0x2B7999C5: None,
    0x063C76AB: "gimmickCorpse",
    0x6B40A33C: None,
    0x04842934: "gimmickSE",
    0x9446EE90: "gimmickBGM",
    0x65663358: None,
    0xF21E3DF2: "gimmickEyepatchArea",
    0x7C065528: "gimmickEnemyDead",
    0x815F9DEF: None,
    0x41CBF846: None,
    0x5E93DEC1: "gimmickBlackMist",
    0x9BDB275E: None,
    0x05112AA4: None,
    0x95F00CDF: None,
    0xF0A0A1B1: None,
    0xE41F82B5: None,
    0xD150D99A: None,  # Has fields: data[0-19] (data[0] has map names)
    0x7A564F60: None,  # Has fields: Model, Motion, Action, Effect, Annotation, Comment
    0xA8030D51: None,  # Has fields: MovePoint
    0xE0114592: None,  # Has fields: startID, endID
    0xE6F796DD: None,  # Has fields: modelName, motionField, motionBattle, motionWeapon, motinoEvent, motionArts00-02, comment
    0xA36067CF: "CHR_PC",
    0xA5A2B4E7: "CHR_Weathering",
    0x175F3C0C: None,  # Has fields: WpnType, UseChr, UseUro, AutoAttack1, AutoAttack2
    0x33F6075F: "BTL_Arts_Camera",
    0xEC03C979: "BTL_Arts_Chain_Set",
    0xE7F1965E: "BTL_Arts_Cond",
    0x3DEC8CBA: "BTL_Arts_En",
    0xE93EBDDC: "BTL_Arts_PC",
    0x38946635: "BTL_ArtsLinkBonus",
    0x7D3620F1: "BTL_ArtsSlowDirection",
    0xCEB9838F: None,  # Has fields: Tank, Attacker, Healer
    0xA5079B0E: None,  # Buff table?  Has fields: Caption, Type, BaseNum, BaseTime, BaseProb, Interval, DirectionID, Effect, EffectID, EffectScale, SE, HealType, NoClear, Icon, NoUro, SpProb
    0x8570C79C: "BTL_Bullet",
    0x72DE28DF: "BTL_BulletEffect",
    0x5095C845: None,  # Has fields: Param (seems to be chain attack gauge gain/loss values)
    0xD9B88F26: None,  # Chain attack order list
    0xA81FEF86: None,  # Has fields: AtkBonus
    0xE337CDEF: None,  # Has fields: Param (seems to be some sort of gain/loss list)
    0xBB82DEE6: None,  # Chain attack TP bonus list
    0xD34EA852: "BTL_Combo",
    0xDC663B47: "BTL_ComboDirection",
    0xAE22B9EF: "BTL_CutInSetting",
    0xAFA559C4: "BTL_DifSetting",
    0x224DB361: "BTL_Element",
    0xFA3E7D62: None,  # Has fields: TankProb1-3, AttackerProb1-3, HealerProb1-3
    0xAD08DF86: "BTL_Enemy",
    0xC1053235: "BTL_EnemyAi",
    0xC6B4111D: None,  # Enemy (unique/event?) drop table
    0xFAB21EAA: None,  # Enemy meat drop table
    0x88BBE290: "BTL_EnemyDrop_Normal",
    0x152F4D70: None,  # Has fields: RevGold
    0x63146EA1: "BTL_EnFamily",
    0x183C80AE: "BTL_Enhance",
    0xCC978CBF: "BTL_EnhanceEff",
    0x963389D1: "BTL_EnParamTable",
    0xA74093B2: "BTL_EnRsc",
    0xB3A34CDB: None,  # Has fields: Frame, COMMAND, Param1-8
    0x4F78EA02: None,  # Has fields: Frame, COMMAND, Param1-8
    0x4453DA7B: None,  # Has fields: Frame, COMMAND, Param1-8
    0x7D46B557: None,  # Has fields: Frame, COMMAND, Param1-8
    0xC8669A3E: None,  # Has fields: Frame, COMMAND, Param1-8
    0xB995827D: None,  # Has fields: Frame, COMMAND, Param1-8
    0xE20FA975: None,  # Has fields: Frame, COMMAND, Param1-8
    0x62B56B76: None,  # Has fields: Frame, COMMAND, Param1-8
    0x2A0AAE73: None,  # Has fields: Frame, COMMAND, Param1-8
    0x55987892: None,  # Has fields: Frame, COMMAND, Param1-8
    0x30BF8916: None,  # Has fields: Frame, COMMAND, Param1-8
    0x61DA793E: None,  # Has fields: Frame, COMMAND, Param1-8
    0x1BD1B16E: None,  # Has fields: Frame, COMMAND, Param1-8
    0x0D55F41E: None,  # Has fields: Frame, COMMAND, Param1-8
    0xB8530CDC: None,  # Has fields: Frame, COMMAND, Param1-8
    0x090BBC2F: None,  # Has fields: Frame, COMMAND, Param1-8
    0x6220E526: None,  # Has fields: Frame, COMMAND, Param1-8
    0x6E79134D: None,  # Has fields: Param (Param: e.g. "se_ch04011010", "arts_swing_medium", "en02011110_eff03")
    0x6BFB2715: None,  # Has fields: Param (looks like a gauge gain list)
    0xD9CA0366: None,  # Has fields: Condition, Param, Subtitling
    0xE312B1C6: "BTL_Grow",
    0x405C97AC: "BTL_HitCameraParam",
    0x659CE1C2: "BTL_HitDirection",
    0xD422E7E2: "BTL_HitEffectBase",
    0xD8678D4C: "BTL_HitEffectSp",
    0xBE8B090C: "BTL_LvRev",
    0xE9E4E964: "BTL_MotionState",
    0x02BF2924: "BTL_Reaction",
    0x64BED5F9: "BTL_RoleAct",
    0x47AEC412: None,  # Has fields: Name, Caption, Type, RangeType, BaseNum, Interval, BaseTime, Effect, EffectID, BulletID, BulletEffID, HealType, Icon - "BTL_SetUp" matches the hash but looks wrong? - might be reaction list for ReActNN in BTL_Arts_*?
    0xE1BC18F7: "BTL_Skill_PC",
    0xEDE2F037: "BTL_RoleSkill",
    0x7ECBAB62: "BTL_Stance",
    0x01ED884D: None,  # Has fields: EffID, MinScale, MaxScale
    0x998A022B: None,  # No known fields
    0x5E12B0D2: "BTL_Talent",
    0x599FEBD8: "BTL_TalentAptitude",
    0xD9D339FE: None,  # Has fields: {Num,Type,Param}01-40
    0xE29EF7E9: None,  # Has fields: PC01-06
    0x73F39787: None,  # Has fields: ChrID, StateName, Hitf, Arts, HitNum
    0x5EBD3829: None,  # Has fields: Name, Role, Lv, Enhance, Icon, Param1-2, TankProb1-3, AttackerProb1-3, HealerProb1-3
    0xBFCFAE86: None,  # Has fields: DefRev, HuardRev, HitRev, AvoidRev, RecastRev
    0xFEFB389B: None,  # Has fields: Param, Param2
    0xD1B7B07E: "BTL_UroTension",
    0x981E4B1E: "BTL_WpnType",
    0xE165A912: "BTL_WpnRsc",
    0x3698A4ED: "BTL_WpnMount",
    0xE0E1A313: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0x15728D92: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0x91F54F44: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0x758629C4: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0xF58F35C6: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0x9A4C2763: None,  # (Ouroboros skill list) Has fields: Name, Type, Param, NeedSp, Link1-5, FormatNo, IconType, UIX, UIY
    0xB2DBA568: "BTL_ChainAttackCam",
    0x533D78EA: "BTL_Achievement",
    0x64D43E80: None,  # Has fields: Target, ConditionType (empty table)
    0xA1621DDF: "BTL_EnSummon",
    0x3FA1EE4F: None,  # Has fields: EnhanceID, Param (looks like skill effect list?)
    0x0578E8B7: None,  # Visual filter list
    0x4725BFF5: None,  # Has fields: UpSpeed, MoveTime, FallRange, FallSpeed
    0x4A6BEB13: None,  # Has fields: mapID, posX, posY, posZ, text
    0x98313F02: "SYS_MapList",
    0x31F6C033: None,  # Has fields: DefaultResource, Condition1
    0xF242AAFD: "FLD_ConditionList",
    0xD5315732: "FLD_ConditionScenario",
    0xDA710DD5: "FLD_ConditionQuest",
    0x88FAB720: "FLD_ConditionEnv",
    0x1AFB9A08: "FLD_ConditionFlag",
    0x3FBC9417: "FLD_ConditionItem",
    0x1218975C: "FLD_ConditionPT",
    0xD17681D6: "FLD_ConditionMapGimmick",
    0x7BBF7CD9: "FLD_ConditionPcLv",
    0xDA7E656A: "FLD_ConditionClassLv",
    0xA971E501: "SYS_ScenarioFlag",
    0x157937BA: None,  # Has fields: resourceFace, resourceHair, resourceBody, resourceAnnotation, IkName, Dirt, sex, physical, race, assign, influence, job, unique, modelType, OffsetId, ColorHair, ColorEye, ColorSkin, MountPath1-4
    0x9590836C: "ITM_Accessory",
    0xB1B9843D: "ITM_Gem",
    0x740FF3CF: "BTL_GemCraft",
    0x34E61888: "ITM_Collection",
    0xDCD7C228: "ITM_Collepedia",
    0xEBE6EBF4: "ITM_Cylinder",
    0x6D2A47CA: "ITM_Extra",
    0x2B0FB3E4: "ITM_Info",
    0x5A69FC7A: "ITM_Precious",
    0xCA4B7760: "ITM_Exchange",
    0x8D233450: "bgmlist",
    0x173D04D6: None,  # Has fields: FieldIcon, MenuIcon
    0xCE3F40EB: None,  # Has fields: MenuIcon
    0x949AA63A: None,  # Has fields: Reward{,Num}1-20, Life, Gold, GoldDivide, SP, BehaviorID
    0xE418C419: "ITM_RewardCollepedia",
    0x49125B68: "ITM_RewardQuest",
    0xD88E0DEB: None,  # Has fields: Colony, RespectPoint, BonusExp
    0xB7136B52: None,  # Has fields: Item{Id,Rate}1-10, ItemCountMin, ItemCountMax
    0xFF63B067: "SYS_DropItemBehavior",
    0xF936594B: None,  # Has fields: Condition, SpotName, Text, IconOffset, Bonfire, [XYZ]Offset
    0xC5C5F70E: None,  # Has fields: Category, FormationCooking, FormationTraining
    0x2521C473: None,  # (Enemy list?) Has fields: MapID, Scale, ChrSize, TurnSize, Level, LevPlus, IdMove, AiBase, IdBgm, MsgName, NPCName, GetRatio, ExpRate, GoldRate
    0xD0DCFD18: None,  # Has fields: EventType, EventID, ContinueEvent, comment
    0xF08FCF57: None,  # No known fields
    0xD880C44D: None,  # (Related to quest item consumption/reward?) Has fields: ItemID, Count
    0xE3AE53B3: None,  # Has fields: Gimmick, Command
    0x09D17C70: None,  # Has fields: ArtsID, Status
    0xF01E66DE: None,  # Has fields: SkillID, Status (empty table)
    0xD0253D11: None,  # Has fields: ChrID, ClassID, ArtsID
    0x8D9A36B7: None,  # Has fields: FlagBit
    0xA263E178: None,  # No known fields
    0x23EE284B: None,  # Event list (10001+)
    0x25B62687: None,  # Event list (15001+)
    0xBB0F57A4: None,  # Event list (16001+)
    0x5B1D40C4: None,  # Event list (20001+)
    0xCC55A8C8: None,  # Has fields: setupName, objName, objType, objID, costume, objModel, wpnBlade, spWeapon
    0x3CF65A32: "EVT_nearfar",
    0xDB0270B0: None,  # Has fields: scenario, event, map (empty table)
    0x98D41CEB: "EVT_MapObjList",
    0x9994480F: "EVT_Place",
    0xABC5B89C: "EVT_HideList",  # FIXME: unclear if correct
    0x065DE649: None,  # Has fields: Character
    0xD8C16C44: None,  # Has fields: Facial, Character
    0xE36B8F14: "EVT_Gradation",
    0x3AE0FC2B: None,  # Has fields: ColorScale, WhiteAddRate
    0x88EF0B3C: "EVT_Vignette",
    0x8B3160C1: None,  # Has fields: Exp, Pos[XY}, Scale[XY}, Wave{Rate,Freq,Random}, StartOffset
    0xFE1D4EF0: "EVT_Color",
    0x81A91D19: None,  # Has fields: name, dist, range, foMin, pixel, lens, strength, blend, pixelLv, hlv, autoFocus, Focus
    0x8ED748D8: None,  # Has fields: ID, scale[XY]
    0x6BB765F3: "EVT_HeroEquip",
    0x07705A00: "QST_List",
    0xFF0E544C: "QST_Purpose",
    0x6F5361AF: "QST_Task",
    0x9D8116C2: "QST_TaskBattle",
    0x0BE50853: "QST_TaskTalk",
    0x5B1907A1: "QST_TaskTalkGroup",
    0x1E0A1725: "QST_TaskEvent",
    0xFCCE91CE: "QST_TaskAsk",
    0x9D8EAB9A: "QST_TaskReach",
    0x2EA5675E: "QST_TaskChase",
    0x49B9F9A4: "QST_TaskRequest",
    0x5AECB721: "QST_TaskCollect",
    0x87C02F98: "QST_TaskCollepedia",
    0x0502353F: "QST_TaskGimmick",
    0x712B265B: "QST_TaskFollow",
    0x8C127EEB: "QST_TaskCondition",
    0x5FE37202: None,
    0x5A6A68B2: None,  # Has fields: Category, Camera, Condition, {PC,Point,Motion,EyeMotion,Mount}1-2, {Object,ObjPoint}1-3
    0xDD6A6032: "SYS_MapPartsList",
    0xAE25EE94: None,  # Has fields: EffectName, Offset[XYZ], Priority
    0x7D09789D: "SYS_MapJumpList",
    0xA3186E4A: "SYS_WeatherRate",
    0x5E53D2EE: "SYS_WeatherList",
    0x9B7727C8: "SYS_WeatherTable",
    0x69F7C5FB: None,  # Has fields: WeatherName, Effect, Se, HudIcon
    0x0EE4CBE3: None,  # Has fields: FamilyTag, AiHungry, AiThirst, AiAnger
    0xE3C4E636: None,  # Has fields: AiFlock, AiFormation, RoleTag, AiHoming
    0x8C492368: None,  # No known fields
    0xDBF04CEB: "FLD_EnMove",
    0xF002B2F5: None,  # Has fields: affType, affName, actionTime1-4, defaultAnim, mountObj, mountTag, mountTag2, enableNopon
    0x1FAD393A: None,  # Has fields: ActionType, Anim, SetAnim, AnimTime, MountObj
    0x76D0D7D9: None,  # Has fields: affType, affName
    0x278B4C72: "RSC_MapObjList",
    0xCA6DB16C: None,  # Has fields: ControlA, ControlB, Visible
    0xFA046DED: None,
    0x3ABF1825: None,
    0xCC1BEC20: "FLD_NpcList",
    0x26C4093B: "FLD_NpcResource",
    0xAF0EFB79: "FLD_NpcTalkList",
    0x7E160E76: "FLD_NpcTalkResource",
    0x64AA3648: None,  # (Possibly: FLD_PcAiMove) No known fields
    0xE40DC263: "FLD_MobList",
    0x965A3DBE: "FLD_MobResource",
    0x7D0E36E4: None,  # Has fields: Physical, Sex, Influence, Job, Race, Unique
    0x3B776F1F: "FLD_InfoList",
    0xBFF821BE: "SYS_OffsetList",  # FIXME: unclear if correct
    0x0B368E78: None,  # Has fields: PartsId, Locations, EffectCondition, EffectStatus, SeName, SeCondition, Offset[XYZ]
    0x0D81DAF8: None,  # Has fields: IconOffset, Interval{Min,Max}
    0xA1AE831D: None,  # Has fields: Range, Angle
    0x121A92C9: None,  # Has fields: Foot[LR]00-02, Placement, Toe, Spine, LookAt, Eye
    0x91A3DC94: "RSC_FootIK",
    0x81ED9E19: "RSC_PlacementIK",
    0x56BD5AC9: "RSC_ToeIK",
    0xE87BEDBD: "RSC_LookAtIK",
    0xA57A8FFB: "RSC_SpineIK",
    0x93BCD4DC: "SYS_AngleKansetu",  # FIXME: unclear if correct
    0x6B3F1942: None,  # Has fields: DefaultOn
    0x1432D8A7: "MNU_dialog",
    0xCD3B3FC3: None,  # Has fields: push_type, action_name
    0xC29E28FD: None,  # Has fields: MenuCategory, Object1, ObjPoint1
    0x02913D16: None,  # Has fields: CaseNoah, CaseMio, CaseEunie, CaseTaion, CaseLanz, CaseSena, HideWeapon
    0x20992C15: "SYS_Mount",
    0xEC6F90EE: "FLD_ObjList",
    0xB1963CFD: "MNU_ShopList",
    0xDCDBDB1F: "MNU_ShopTable",
    0xB1902C5B: None,  # Has feilds: {StartEvent,ReactionEvent,Condition,Repeatable,EndFlag}1-6
    0x83E0F284: None,  # Has fields: Grouping, {Character,VoiceID,Text,Time}1-5
    0xDAF44E8F: None,  # Has fields: Grouping, Character, VoiceID, Text, Spot, Info, Item
    0xFEF315B6: None,  # Has fields: EventID, Condition, SpotGimmick
    0xF9349351: None,  # Has fields: icon_index, type, obj_name, disp_range, disp_check
    0xFF057327: "CHR_UroBody",
    0xE44BEAA2: None,  # Has fields: PC, PointType, Motion, EyeMotion, MountObj
    0x0828980E: "FLD_ColonyList",
    0x22F5273E: None,  # Has fields: NpcID, Collepedia{,Condition}1-3, Condition1-3, Comment
    0x5A744A5C: None,
    0x85A8179F: None,  # Has fields: ColonyID, Point, Comment
    0x7E6F5DCC: None,  # Has fields: name, hint, icon_index, menu_command, menu_value
    0x1A109460: None,
    0x7CE82B08: "MNU_saveload_scenario",
    0x2DA282E2: "MNU_game_option_category",
    0x32DBEBED: None,
    0xAA2FA6DE: "MNU_EquipDetail",
    0xEF81AE52: None,  # Has fields: DetailText1-6
    0xF185DC10: None,  # Has fields: Model, Motion, OffsetId, IkName
    0x92D8F17B: "FLD_RelationNpc",
    0x938A4DD1: "FLD_RelationColony",
    0x4B91D8C8: None,  # Has fields: EventID, Comment
    0x2BBE255B: None,  # Has fields: {NpcID,value}1-6, Comment
    0xE1C78647: None,  # Has fields: {ColonyID,value}1-3, Comment
    0x861D003A: None,  # Has fields: {RelationID,value}1-10, Comment
    0xFAC1F258: None,  # Has fields: {RelationID,value}1-4, Comment
    0xC80D5841: "FLD_AffCollection",  # FIXME: unclear if correct
    0xCB74AC0D: "SYS_GimmickLocation",
    0x35454DAE: "SYS_PreciousIDGimmick",
    0x8F29BCAF: None,  # Has fields: GimmickID
    0x15DE3DDF: None,  # Ferronis hulk startup costs
    0x6EDF0096: None,  # (Possibly related to 2500 Ether Cylinder quest?) Has fields: Cylinder, ItemCountMin, ItemCountMax, Item
    0x7729B35C: None,  # Has fields: Condition, Item{Id,Rate}1-10
    0x0A316038: "FLD_CookRecipe",
    0xAF5A7B80: "FLD_CraftCookList",
    0x0D4DD27E: None,  # Has fields: SpotGimmick, TableID, Comment
    0xF02EB97C: None,  # Recipe upgrade list
    0x6EC8096C: None,  # Canteen recipe list
    0x3B47669B: "QST_RequestItemSet",
    0x1FCFB323: None,  # Has fields: {Condition,BGM}1-4
    0x2CFCAF13: None,  # No known fields
    0x65ACA8AC: "SYS_SystemOpen",
    0x5611DDA6: "MNU_GuestIconList",
    0x7C8EEF72: None,  # Has fields: eff_col
    0x90A6221A: None,  # Has fields: Interval, Priority, EndCheckType
    0xE6E60A3E: None,  # (Voice replacement list?) Has fields: TargetFile, Condition, ChangeFile
    0xF95843F9: None,  # Has fields: Group, ChrType, ChrID, UroID, Change, Cond1-2, LotRate, Reply, ReplyGroup, Voice1-4, RandPC, RandHero, Param1-2, TimeZone
    0x6707EF65: None,  # Has fields: Group, ChrType, ChrID, UroID, Change, Cond1-2, LotRate, Reply, ReplyGroup, Voice1-4, RandPC, RandHero, Param1-2, TimeZone
    0x8F85EC10: None,  # Has fields: Group, ChrType, ChrID, UroID, Change, Cond1-2, LotRate, Reply, ReplyGroup, Voice1-4, RandPC, RandHero, Param1-2, TimeZone
    0x52898612: None,  # Has fields: {MotionState,Motionf,Voice}1-8
    0xBCB34762: "MNU_TipsList",
    0xF1E32CAF: "MNU_QuestTask",
    0x96ECF5BF: "MNU_InputAct",
    0xFB06EACE: "MNU_InputPad",
    0x38031E0F: None,  # Has fields: Interval, Damage
    0x6F56B53C: "SYS_CameraShake",
    0xA5595837: None,  # Has fields: Main, Soup(?), Center1, Center2
    0xEED24855: None,  # Unique monster list
    0x13B8DA8C: None,  # Has fields: GraveID, EndCheck
    0x3CC7CE2D: "FLD_ConditionTutorial",
    0xAA6D70CA: "MNU_MapInfo",
    0xD5696E7F: "MNU_MapInfoFile",
    0x35D68F4D: None,  # Has fields: BoneName1-4, StepOffset, Vibration
    0xF0F61B4E: None,  # Has fields: StepOffset1-4
    0x06955984: None,  # Has fields: Walk, Run, LandingDamage, Slide
    0x5AC778BE: None,  # Has fields: Default, Soil, Sand, Grass, Wood, Iron, Snow, Carpet, Gel, Gravel, Water, Shallows, InWater, Mist
    0xEE61112B: "FLD_LookAt",  # FIXME: unclear if correct
    0xFB616D5F: "SYS_CharacterDirection",
    0x6009A5C3: "SYS_CommonDirection",
    0x2BE55EEA: "SYS_UniqueDirection",
    0x9ADB8D4C: "SYS_DirectionBranch",
    0x473B9203: "SYS_DirectionParam",
    0xCBF26BB3: None,  # Has fields: Name, Caption, Type, Comment
    0xC2CE883D: None,  # Has fields: Type, Value1-20, Comment
    0xDB31DA53: None,  # Has fields: {Name,Caption,Type,Value}1-3, Time, Comment
    0x67BCB6FE: "SYS_CommonEffect",
    0xC2C2933F: None,  # Has fields: Character, {Motion,Probability}01-05
    0xAD80BED6: None,  # Has fields: Motion, MaxValue
    0xC60C0FBD: None,  # Has fields: Category, ValueOffset, ToonID(?), Comment
    0xE9E95941: None,  # Has fields: Category, ValueOffset, ToonID(?), Comment
    0xCFC17118: None,  # Has fields: Category, ValueOffset, ToonID(?), Comment
    0x40A97F5D: "FLD_PcFormation",
    0xB8A49792: "FLD_NpcTalkAction",
    0x32E3254F: "QST_NaviMapList",  # FIXME: unclear if correct
    0x03B52788: None,  # (Tutorial battle list) Has fields: Comment, Tutorial, Title, Thumbnail, Summary, Leader, Party, Condition
    0xF9173812: None,  # (Tutorial battle party list) Has fields: Comment, {PC,Level,ArtsSet}01-06, HERO, LevelHero
    0xA3CAD8C7: None,  # (Tutorial battle arts set list) Has fields: Talent, arts01-06
    0x8C1FA2DE: "SYS_Tutorial",
    0x03DB7192: "SYS_TutorialEnemyInfo",
    0x7DEB6EAF: "MNU_HeroList",
    0xC76D3FE4: "SYS_TutorialHintA",
    0x15067E12: "SYS_TutorialHintB",
    0x435B94E7: None,  # Has fields: IconType, IconNo, Title
    0x3D5EC9E5: "SYS_TutorialTask",
    0x4E31A784: None,  # Has fields: Intensity, StartOffset
    0x6F42026E: None,  # Has fields: ColorScale, WhiteAddRate
    0x5750277F: None,  # Has fields: Exp, Pos[XY], Scale[XY], Wave{Rate,Freq,Random}, StartOffset
    0x6BD7030D: "FLD_Vignette",
    0xD465E6B7: None,  # Has fields: Gimmick
    0xDE695AF0: None,  # Has fields: cam_l[xyz], cam_angle
    0xCA4DD4C0: "SYS_SpAttack",
    0x72C56041: None,  # Has fields: {PC,Motion,Object}1-2
    0xD327B2BC: None,  # Has fields: QuestID, TaskID, Comment
    0xC672E6FC: "SYS_Vibration",
    0x7147D811: "FLD_MobScale",
    0xB52CB42D: None,  # Has fields: Before, Condition, After
    0x96AE47E6: "SYS_TutorialWaitTime",
    0x8E6B2295: None,  # Has fields: Category
    0xF5EB8697: None,  # Has fields: MaxNumber, AddLv01-10
    0xE6D8A7AE: "MNU_EventTheater_scn",
    0xD52EFD79: "MNU_FlagParam",
    0x09D4E3FD: None,  # Has fields: name ("fade_past_memory_short", "ma09a_gim_thunder" etc), comment
    0x4DA4962C: None,  # Has fields: NPC, InfoPiece
    0xF9828127: None,  # Has fields: MsgID, Comment
    0x9BF7EEDC: "FLD_EnemyAff",
    0xD147C68F: "SYS_TutorialSummary",
    0x7D70A887: "SYS_TutorialArrow",
    0x39D667D1: None,  # (Possibly: RSC_PcCostumeOpen) Has fields: Talent, Flag1-6, Name1-6, DLC
    0xCF66EB21: "QST_QuestImageList",
    0xB971C420: None,  # Has fields: Talent, ArtsID, Special
    0x5F654D94: None,  # Has fields: Talent, SkillID
    0xAFD8D84D: None,  # Has fields: Type, R, G, B, Time, WaitEnd
    0xB93870C8: "SYS_TutorialMessage",
    0x2177D111: "MNU_VoiceList",
    0xE15A6DE7: None,  # Has fields: RewardA1-2, RewardB1-2
    0xA8FEE5F0: "MNU_UroSkillList",
    0xAFD83F1B: "MNU_Attachment",
    0x8CA278B0: "SYS_LoadingTips",
    0x08EF7F06: None,  # Has fields: name, ScenarioFlag
    0x74385681: None,  # Has fields: PcID, TalentID, ArtistName, WeaponName, Voice1-4, ArtsVoice1-6, Arts1-6
    0xC810A4F3: None,  # Has fields: NumberingID, OpenFlag, LotID, RewordName, RewordText
    0x2FE3444A: "BTL_AutoSetAccessory",
    0xFA253EBF: "BTL_AutoSetArts",
    0x139348CC: "BTL_AutoSetGem",
    0x13DED235: "BTL_AutoSetSkill",
    0x1D96E424: None,  # (Possibly: MNU_QuestNotSell) Has fields: Condition, Item01-10
    0x7A066663: None,  # Has fields: TaskID, MapID, Comment
    0xE7251BBB: "MNU_MapSlide",  # FIXME: unclear if correct
    0x3D608A6E: "MNU_QuestFollow",
    0xA6AAF689: None,  # Has fields: PcID, ArtsID
    0x5CD15665: None,  # (Possibly DLC related?) Has fields: DescText, ImageID, ImageNum, SortID, Comment
    0xDA526616: None,  # (Possibly DLC related?) Has fields: VolID, TitleText, DescText, ImageID, SortID, Comment
    0x1623B3A0: None,  # (Possibly DLC related?) Has fields: ContentsID, DispType, DescText, ImageID, SortID, Comment
    0xA970CAF5: "MNU_DlcGift",
    0xCED21F4E: "MNU_PatchInfo",
    0xB150F956: "MNU_PatchDetailA",
    0xF8B54C2C: "MNU_PatchDetailB",
    0x19C1C36F: None,
    0xC89242D1: None,
    0x825EDC88: None,
    0x7E210829: None,
    0x42FEA196: "msg_btl_arts_en_name",
    0xAC73A945: "msg_btl_arts_name",
    0x7CF9D610: None,
    0xF8F0A001: None,
    0xF6E689C3: None,
    0xFC27D14D: None,
    0xA391C96F: None,
    0xAA84C456: "msg_btl_enhance_cap",
    0x7907F75E: None,
    0x455071CB: None,
    0x56FFF926: None,
    0xDC74E779: None,
    0x77B6A0EF: None,
    0xD96BDBBA: None,
    0xEAD5D4A9: None,
    0xEA640EBA: None,
    0x0E3090DA: None,
    0x8B7D949B: None,
    0x0103F5B8: None,
    0x621C6EF4: None,
    0x4187FB3B: None,
    0x595F9BFC: None,
    0xDA793D25: None,
    0x51036BF4: None,
    0x2C124487: None,
    0xE2C3F848: None,
    0xBCCDD7A5: None,
    0x34233CF2: None,
    0x8E175A1F: None,
    0xB8F58D39: None,
    0x32E2F16E: None,
    0x8554022B: None,
    0x2A9BD580: "msg_mnu_common_ms",
    0x10F03A79: None,
    0x23E826C6: None,
    0xDF7177AE: None,
    0xABB95378: None,
    0x23A3F9FA: None,
    0x9B6C0A66: None,
    0x39FD0CD1: None,
    0x1B7362AD: "msg_mnu_generic_window_ms",
    0x1B0E6B3B: None,
    0x0D7447C1: None,
    0x9760BC94: None,
    0x4A652F33: None,
    0xE1298BC4: "msg_mnu_key_explanation",
    0x912A4988: None,
    0x73566A46: "msg_mnu_mainmenu",
    0xF1CBAC59: None,
    0x5DFDA895: None,
    0xA61679BA: None,
    0xAAEBE79E: None,
    0x5FEC6350: None,
    0x1F0DC7C2: "msg_mnu_operation_guide",
    0x5F68C7D2: "msg_mnu_option",
    0x83AAF628: None,
    0x0B8B0747: None,
    0x754D1494: None,
    0xB7001BB1: None,
    0x277983C9: None,
    0x6E048BD1: None,
    0xC61BE14B: None,
    0x5C52C972: "msg_mnu_style_standard_ms",
    0x29821FC5: None,
    0x6D15742F: None,
    0x2902008F: None,
    0xBBF540E7: None,
    0xA1A111AE: None,
    0xEA19B333: "msg_qst_RequestItemSet",
    0x45A2D5AD: None,
    0xAD40857C: "msg_qst_task",
    0xC617D216: None,
    0x9B911635: None,
    0x4F89C921: None,
    0x4ACCBB53: None,
    0x4CF32197: None,
    0x122A06D4: None,
    0x65FD1C43: "msg_enemy_type_name",
    0x66DEC3A2: None,
    0x9AA4C028: None,
    0x133CD173: None,
    0xBEDB6533: None,
    0x24810A75: None,
    0x6E269557: None,
    0x16630085: None,
    0xD0A5476B: None,
    0xCA2198EC: None,
    0x3550B295: None,
    0x33C3A247: None,
    0x06CEE8EA: None,
    0x32601547: None,
    0x28E8B08C: None,
    0x6436BD4A: None,
    0xEDFB4E9F: None,
    0xBA34C46E: None,
    0x16B245E3: None,
    0xE48A94FF: None,
    0x3BEB99D8: None,
    0x1BBC9E6B: "msg_tutorial_ui",
    0x8EF4CF86: None,
    0x331C38A9: None,  # Nonexistent file (but listed in the program)
    0xA942668F: None,  # Nonexistent file (but listed in the program)
    0x3F3EBDB4: None,  # Nonexistent file (but listed in the program)
    0xFD25F733: None,
    0xD633C26E: None,
    0xF17757AB: None,
    0x7385D29E: None,
    0xF724F13C: None,
    0x133B3027: None,
    0x2B2AAECA: None,
    0x6F99D9D6: None,
    0x50219162: None,
    0xF685A94E: None,
    0x981E9686: None,
    0xBF147F74: None,

    # Other table names:
    0xDB3F6A13: "BTL_Ai",
    0xB5B61435: "BTL_FA_Prm01",
    0xF350A3E5: "BTL_FA_Prm02",
    0xC93F0967: "BTL_FA_Prm03",
    0x903C4F6B: "BTL_FA_Prm04",
    0xA6D481B1: "BTL_FA_Prm05",
    0x4A7F0ABE: "BTL_FA_Prm06",
    0xB25E81A9: "BTL_FA_Prm07",
    0xCE4989DD: "BTL_FA_Prm08",
    0x39E57974: "BTL_FA_Prm09",
    0x7E3D9C71: "BTL_FA_Prm10",
    0xB40B5F04: "BTL_FA_Prm11",
    0x5D9F1225: "BTL_FA_Prm12",
    0xFC178762: "BTL_FA_Prm13",
    0xACABE7A5: "BTL_FA_Prm14",
    0x9917A283: "BTL_FA_Prm15",
    0xB7A3CAD7: "BTL_FA_Prm16",
    0x00D58307: "BTL_FA_Prm17",
    0x9C3EBC4A: "BTL_FA_Prm18",
    0x37C1077E: "BTL_FA_Prm19",
    0xE9008F12: "BTL_FA_Prm20",
    0x11F3AE13: "BTL_FA_Prm21",
    0x3350571B: "BTL_FA_Prm22",
    0xFA1E142D: "BTL_FA_Prm23",
    0x823474FB: "BTL_FA_Prm24",
    0x0C2B40C0: "BTL_FA_Prm25",
    0xB8770FA6: "BTL_FA_Prm26",
    0x1CEFCA4A: "BTL_FA_Prm27",
    0x3E1EF073: "BTL_FA_Prm28",
    0x07F3243D: "BTL_FA_Prm29",
    0xC7993641: "BTL_SystemBalance",
    0x1BE05692: "BTL_TL_PrmRev01",
    0x84073E32: "BTL_TL_PrmRev02",
    0xCE66DFE9: "BTL_TL_PrmRev03",
    0x23CF7909: "BTL_TL_PrmRev04",
    0x46C05B6E: "BTL_TL_PrmRev05",
    0xCD5509A5: "BTL_TL_PrmRev06",
    0x934AA80D: "BTL_TL_PrmRev07",
    0xBF4EA1B8: "BTL_TL_PrmRev08",
    0xBF4EA1B8: "BTL_TL_PrmRev08",
    0xBB5036F7: "BTL_TL_PrmRev09",
    0x9449008E: "BTL_TL_PrmRev10",
    0xE10FBA8D: "BTL_TL_PrmRev11",
    0xDBA9FA90: "BTL_TL_PrmRev12",
    0x32AE7B9A: "BTL_TL_PrmRev13",
    0x0FD802C5: "BTL_TL_PrmRev14",
    0x6E8E2F9C: "BTL_TL_PrmRev15",
    0x0D38ED98: "BTL_TL_PrmRev16",
    0x1CA60603: "BTL_TL_PrmRev17",
    0xA1FA5E91: "BTL_TL_PrmRev18",
    0xD5230761: "BTL_TL_PrmRev19",
    0x681F1E1D: "BTL_TL_PrmRev20",
    0x521BEF78: "BTL_TL_PrmRev21",
    0x93FA1C52: "BTL_TL_PrmRev22",
    0x487D1AD0: "BTL_TL_PrmRev23",
    0x8E0066B2: "BTL_TL_PrmRev24",
    0x86453FF9: "BTL_TL_PrmRev25",
    0x568D44E5: "BTL_TL_PrmRev26",
    0x2C8C5004: "BTL_TL_PrmRev27",
    0x55F60607: "BTL_TL_PrmRev28",
    0xD0FE369E: "BTL_TL_PrmRev29",
    0xCE6B3ED3: "BTL_TL_PrmRev30",
    0xA7EAC207: "BTL_TL_PrmRev31",
    0x310AE49E: "BTL_WpnParam01",
    0x71FCA5C7: "BTL_WpnParam02",
    0xE00E4C3C: "BTL_WpnParam03",
    0xCDEAE542: "BTL_WpnParam04",
    0x7CB63A6B: "BTL_WpnParam05",
    0xEC1897D5: "BTL_WpnParam06",
    0x08751178: "BTL_WpnParam07",
    0x899DC858: "BTL_WpnParam08",
    0xFBCE40A6: "BTL_WpnParam09",
    0x8D701581: "BTL_WpnParam10",
    0xDBC706B7: "BTL_WpnParam11",
    0xEDC29038: "BTL_WpnParam12",
    0x57023D16: "BTL_WpnParam13",
    0xFB089424: "BTL_WpnParam14",
    0xEAA794AC: "BTL_WpnParam15",
    0x3C1FA698: "BTL_WpnParam16",
    0xF05F5D8C: "BTL_WpnParam17",
    0x902E7B65: "BTL_WpnParam18",
    0xDCEDF3EF: "BTL_WpnParam19",
    0x08D37B00: "BTL_WpnParam20",
    0xF9008831: "BTL_WpnParam21",
    0xF226719F: "BTL_WpnParam22",
    0xBA9BC5A5: "BTL_WpnParam23",
    0x2A8109F3: "BTL_WpnParam24",
    0x2FD46401: "BTL_WpnParam25",
    0xCEE25938: "BTL_WpnParam26",
    0x47AD0EB4: "BTL_WpnParam27",
    0xF4E47BBA: "BTL_WpnParamS1",
    0x08AE1617: "BTL_WpnParamS2",
    0xAFC80603: "BTL_WpnParamU1",
    0xE27CBB9E: "BTL_WpnParamU2",
    0xA436E304: "BTL_WpnParamU3",
    0x0EE98229: "BTL_WpnParamU4",
    0xC82B9EDC: "BTL_WpnParamU5",
    0x1C97E25E: "BTL_WpnParamU6",
    0x6EE6EE72: "CHR_TopProb",  # FIXME: unclear if correct
    0x541B26AD: "FLD_RelationArrow",
    0xF8207CBA: "MNU_FacePatternList",
    0xD90FF31C: "MNU_FontSet01",
    0x06079AEA: "MNU_FontSet01_cn",
    0x0CFF6E6B: "MNU_FontSet01_kr",
    0x8543AF98: "MNU_FontSet01_tw",
    0x2CB06FE9: "MNU_Layer",
    0x5645DB7F: "MNU_ResFont",
    0x56E714AA: "MNU_ResFontStyle",
    0x2DD45C21: "MNU_ResImage",
    0xE92E9F68: "MNU_ResLayout",
    0xAB68D046: "MNU_ResMSProj",
    0xF8103211: "MNU_ResourceCategory",
    0x2B760A8C: "MNU_ResourceType",
    0x4CF1C296: "MNU_TextLink_Mstxt",
    0xE1E61948: "MNU_Text_IdList",
    0x686FDFDB: "MNU_filter",
    0xD4D03C1E: "MNU_sort",

    0x9416AC93: "1",
    0x0129E217: "2",
    0x0FC7A1B4: "3",
    0xE131CC88: "4",
    0x531A35E4: "5",
    0x27FA7CC0: "6",
    0x23EA8628: "7",
    0xBD920017: "8",
    0x248BE6A1: "9",
    0x86E4093F: "10",
    0x989CDBB2: "11",
    0xF9D2EF15: "12",
    0xB74D5141: "13",
    0x97BFE639: "14",
    0xD66FFCFC: "15",
    0xC3A56D70: "16",
    0x6E6F0B04: "17",
    0x3ADA2F46: "18",
    0x5AA1C0D3: "19",
    0xF647A258: "20",
    0x47F4EF7A: "21",
    0xED667DCC: "22",
    0x650E5121: "23",
    0x845119E8: "24",
    0x4A48B9DC: "25",
    0x1D72E99B: "26",
    0xADA3168A: "27",
    0x82151E2E: "28",
    0x57F73152: "29",
    0x2CA6CE8E: "30",

    0x5E097F2E: "AITag",
    0x085A7B72: "AchieveType",
    0x4E395239: "AchievementCount",
    0x04917EC1: "AclEnd",
    0x97530FCC: "AclStart",
    0x7C61794C: "ActSpeed",
    0xEDA5DA5B: "ActType",
    0xF59B6FEA: "Action",
    0x234F4F14: "ActionType",
    0x9EEA5C71: "AddCondition1",
    0x3D3E9434: "AddCondition2",
    0x0403A96F: "AddCondition3",
    0xA605EA11: "AddCondition4",
    0x354AD7B2: "AddCondition5",
    0x18168DEE: "AddCondition6",
    0xF4C7CCCB: "AddCondition7",
    0xE5FA157E: "AddCondition8",
    0x6A2CBA91: "AddCondition9",
    0x0954D68D: "AddCondition10",
    0xEBC03FF2: "AddCondition11",
    0x609CFA35: "AddCondition12",
    0x25CF98AE: "AddCondition13",
    0xC30F6AF2: "AddCondition14",
    0xB4E3B48F: "AddCondition15",
    0x22E75E8C: "AddCondition16",
    0x275864C5: "AddCondition17",
    0xEC32C9A1: "AddCondition18",
    0x642FF971: "AddCondition19",
    0x3609DADD: "AddCondition20",
    0xDD7BC38E: "AddLv01",
    0x66C7BA45: "AddLv02",
    0xCB159A4C: "AddLv03",
    0x7329BFC3: "AddLv04",
    0x393DFF11: "AddLv05",
    0xBB9B0685: "AddLv06",
    0xB6D54F52: "AddLv07",
    0xBBCCD019: "AddLv08",
    0xAC4337F3: "AddLv09",
    0xAAAA748C: "AddLv10",
    0x81F10D0F: "AddValue1",
    0x8DE3B053: "AddValue2",
    0xDC0476F7: "AddValue3",
    0x5CEC3701: "AddValue4",
    0x16239741: "AddValue5",
    0x0126A47B: "AddValue6",
    0x3795FA41: "AddValue7",
    0xD62FA1AE: "AddValue8",
    0xDACD2796: "After",
    0x57B5DD7C: "Age",
    0xC206D2B1: "AgilityBase",
    0x4D38AB2A: "AgilityLv1",
    0xCE806F4A: "AgilityLv99",
    0x7AE39FD7: "AgilityRev",
    0xA83E3948: "AgilityRev1",
    0x566C3278: "AgilityRev2",
    0xA93E1490: "AgnusRate",
    0x87654CBF: "AgnusReward",
    0x72B1CF12: "AiAnger",
    0xF2937403: "AiBase",
    0x1022F1D3: "AiCond1",
    0xEB0CD34F: "AiCond2",
    0x28930671: "AiCycle",
    0x0120A870: "AiFlock",
    0xAA907FD1: "AiFormation",
    0x55ACF3FA: "AiHoming",
    0x46A683E1: "AiHungry",
    0xC286B0CC: "AiID",
    0x14248229: "AiParam1",
    0xB663DB4B: "AiParam2",
    0x9009B6B3: "AiRate1",
    0xF3E38D03: "AiRate2",
    0x50D4E252: "AiRole",
    0x0A1AE34A: "AiSetting1",
    0x29307AEC: "AiSetting2",
    0xCB7CAE57: "AiSetting3",
    0xC1E75F48: "AiSetting4",
    0x535F90E6: "AiSetting5",
    0x5640E05E: "AiSetting6",
    0x91473648: "AiThirst",
    0xC42FC5B4: "Angle",
    0xDDFEDC12: "AngleDeg",
    0x09CE7D35: "Anim",
    0x38F5029C: "AnimTime",
    0x55D02483: "Annotation",
    0xB688209A: "AnnotationName",
    0x9EE7227C: "Any",
    0x67BBAD5B: "AppMot1",
    0x3DB0238F: "AppMot2",
    0xACF0AA65: "AppMot3",
    0x568E34ED: "AppMot4",
    0xFB03475A: "AppMot5",
    0x581A8650: "AppMot6",
    0x7698141C: "Appear",
    0x045C6899: "AppearScale",
    0xC36BF063: "Appearance",
    0xEFD483D9: "Argument1",
    0x62B6A631: "Argument2",
    0xCF45505F: "ArrowDir1",
    0xD063B5DD: "ArrowDir2",
    0x3B5DA661: "ArrowDir3",
    0x31173B6C: "ArrowDir4",
    0xFF4DA1AE: "ArrowDir5",
    0x9271FD5D: "ArrowType1",
    0xE1EFA90D: "ArrowType2",
    0xAD55EA7C: "ArrowType3",
    0x85459AE6: "ArrowType4",
    0x7400608F: "ArrowType5",
    0x81E0483B: "ArtistName",
    0xC2A50178: "Arts",
    0x04F6A73D: "Arts1",
    0xFF31413D: "Arts2",
    0xE2CEC6EC: "Arts3",
    0xCA298A54: "Arts4",
    0xC341AFEB: "Arts5",
    0xE5FB1843: "Arts6",
    0x16CE8F24: "ArtsCategory",
    0x453BBF2B: "ArtsID",
    0x2FC5B154: "ArtsNo",
    0x82A6D407: "ArtsSet01",
    0x2C32E5B0: "ArtsSet02",
    0xA6A893ED: "ArtsSet03",
    0x5F5F32EB: "ArtsSet04",
    0xB91F7464: "ArtsSet05",
    0x30D2D667: "ArtsSet06",
    0x686F16D8: "ArtsSlot0",
    0xC761DA46: "ArtsSlot1",
    0xF19664A4: "ArtsSlot2",
    0x7880DE81: "ArtsSlot3",
    0x2D7892A8: "ArtsSlot4",
    0x3195BF16: "ArtsSlot5",
    0x5748A0F8: "ArtsSlot6",
    0xC7586F91: "ArtsSlot7",
    0xA094F6CF: "ArtsSlot8",
    0x7B121DAB: "ArtsSlot9",
    0x3ACE7853: "ArtsSlot10",
    0x56046D53: "ArtsSlot11",
    0x2E1828C1: "ArtsSlot12",
    0x0370178A: "ArtsSlot13",
    0x22758A44: "ArtsSlot14",
    0x9489AAD1: "ArtsSlot15",
    0x93C58FAC: "ArtsType",
    0xD3855917: "ArtsVoice1",
    0xCA233721: "ArtsVoice2",
    0xDA75EA31: "ArtsVoice3",
    0xA4404DDD: "ArtsVoice4",
    0x0A96E6F8: "ArtsVoice5",
    0xB1279E3B: "ArtsVoice6",
    0xDF9E4AE7: "AspectRatio",
    0x650AF65A: "Assign1",
    0x0EF4F03C: "Assign2",
    0x1EF4E151: "Assign3",
    0x58FAE3F4: "Assign4",
    0x18FA8D52: "Assign5",
    0x57DC95FF: "Assign6",
    0x2522EC6F: "Assign7",
    0x963DA434: "Assign8",
    0xFA8531C2: "Assign9",
    0xA1F5936C: "Assign10",
    0x9655E79C: "Assign11",
    0x4DF82141: "Assign12",
    0xBE929E8D: "Assign13",
    0x58EA9BD5: "Assign14",
    0x70F95E7C: "Assign15",
    0xA9DAA9D4: "Assign16",
    0x4336108C: "Atk",
    0xE039A529: "AtkBonus",  # FIXME: unclear if correct
    0xAA16BC6B: "AtkHeal",
    0xA744C97B: "AtkRev",
    0x1221C4ED: "Atr",
    0xA83519F9: "AttackType",
    0x1EF9D95D: "Attacker",
    0xF43BA09E: "AttackerProb1",
    0xE398E2E3: "AttackerProb2",
    0x19539F40: "AttackerProb3",
    0x944D4D65: "Attenuation",
    0xEEB398A0: "AttenuationScale",  # FIXME: unclear if correct
    0xD8B07410: "AutoAttack1",
    0x8DC7FEE3: "AutoAttack2",
    0x039647DD: "AutoSet1",
    0x8BAD6AC6: "AutoSet2",
    0x894CA6BB: "AutoSet3",
    0xBBD24652: "AutoSlot0",
    0xEBFCC1AC: "AutoSlot1",
    0xE5575DCE: "AutoSlot2",
    0x24CC0315: "AutoStart",
    0x12C8988F: "AvoidRev",

    0xCCA66A8A: "B",
    0x967EF440: "BGM1",
    0x904CDF05: "BGM2",
    0xDAE723DC: "BGM3",
    0xC5101EA7: "BGM4",
    0xC32883FD: "BaseEnemy",
    0xDDF9618D: "BaseNum",
    0x594242A6: "BaseNum2",
    0xED10BAF9: "BaseNum3",
    0x38025F91: "BaseProb",
    0xCCB52419: "BaseRecipe",
    0x23C6CBED: "BaseResource",
    0xD622A439: "BaseTime",
    0x96802080: "BattleCategory",
    0x27DD2297: "Before",
    0x64FCF627: "BeforeWeather",
    0xE9E2E301: "BehaviorID",
    0xD9D73B99: "BgmCondition",
    0x40EB635C: "BlendMul",
    0xA57B7227: "BltMaxAng",
    0x36254CF7: "BoneCamera",
    0xDDF64FCD: "BoneCenter",
    0x0519546B: "BoneName",
    0x3EDA0A22: "BoneName1",
    0x49529FA5: "BoneName2",
    0x38A4AD0B: "BoneName3",
    0x77A593D0: "BoneName4",
    0xC6F4CF04: "Bonfire",
    0xD0132639: "BonusExp",
    0xFB07B028: "Bounds",
    0x7CAF8348: "Branch1",
    0x8F4E0F37: "Branch2",
    0x1C25ECF7: "Branch3",
    0xDE966711: "Branch4",
    0x003CCC2F: "BranchID",
    0x59F6B911: "Bullet",
    0xDB0231EC: "BulletAngle",
    0xE97DCA60: "BulletEffID",
    0x3576BE77: "BulletID",
    0xF5124EA5: "BulletNum",
    0xAC95B9B7: "BulletScale",

    0x855B9573: "COMMAND",
    0x6D759202: "CallEventA",
    0xB510038F: "CallEventB",
    0xE464F1FC: "CallMsg",
    0xF5F4651F: "CamAngle",
    0x146A1C4B: "CamType",
    0x06C42ABF: "Camera",
    0xFD239BB8: "Camera01",
    0x27224887: "Camera02",
    0x0C9B9D76: "Camera03",
    0x7332BFD8: "Camera04",
    0xD792F439: "Camera05",
    0x180097BE: "Camera06",
    0x0068B798: "Camera07",
    0x8F8322C6: "CameraDirection",
    0xA6841FFF: "CameraTable",
    0x26F3523B: "Caption",
    0x19C4389C: "Caption1",
    0x39B0054D: "Caption2",
    0x95827790: "Caption3",
    0x7C06F6F8: "Carpet",
    0x537D98F9: "CaseEunie",
    0x206A47B3: "CaseLanz",
    0x0F56C7FE: "CaseMio",
    0xBD30E046: "CaseNoah",
    0xF4C2CE83: "CaseSena",
    0x10391E96: "CaseTaion",
    0xAB8D5038: "CatMain",  # FIXME: unclear if correct
    0x689B60B2: "Category",
    0xD8485D1F: "CategoryPriority",
    0x1FAF3916: "Center1",
    0xC276278D: "Center2",
    0x005FD5C3: "ChainArts",
    0xA49EBFA0: "ChainOrder",
    0x5781C0FE: "ChainUp",
    0x57CF2FBE: "Change",
    0xEA271ECB: "ChangeFile",
    0x372B6726: "Chapter",
    0xEABBB65C: "Character",
    0x23FF3AA9: "Character1",
    0xD71F2B53: "Character2",
    0x6F2F9D5E: "Character3",
    0xB184C8B0: "Character4",
    0xE7DD569B: "Character5",
    0xC995F890: "CheckFlag1",
    0x57E01ED3: "CheckFlag2",
    0x64248957: "CheckFlag3",
    0x2D4EED51: "CheckFlag4",
    0x36313E37: "CheckFlag5",
    0x757E9F0F: "CheckFlag6",
    0x65DFDE70: "CheckFlag7",
    0xF8DF4196: "CheckFlag8",
    0xC6719F12: "CheckView",  # FIXME: unclear if correct
    0xC5CFF8E4: "ChestHeight",
    0xA31D2886: "ChrID",
    0x753413DC: "ChrSize",
    0xDF7C29E2: "ChrType",
    0xCD123CC1: "ClassID",
    0xAFBC9389: "CloseEffect",
    0x82E7EFEB: "CollectionID",
    0x3EE2AE1D: "CollepediaCondition1",
    0xD4D5A16F: "CollepediaCondition2",
    0x6943717C: "CollepediaCondition3",
    0xA8626A8A: "CollepediaID",
    0x6F003460: "Colony",
    0xA2D9F858: "ColonyID",
    0xF9287E80: "ColonyID1",
    0x7FAA81FB: "ColonyID2",
    0x144A602C: "ColonyID3",
    0xCC59D227: "Color",
    0x3566BD5E: "ColorB",
    0x352A786D: "ColorEye",
    0x62449319: "ColorG",
    0xCBEDF772: "ColorHair",
    0x71ED382C: "ColorR",
    0x2BB832A4: "ColorScale",
    0x3F14D64E: "ColorSkin",
    0x57A87F30: "ComboStage",
    0x7CC7F79F: "Command",
    0x890BD622: "Comment",
    0xEF714D2B: "Comment1",
    0xEF0853FC: "Comment2",
    0xE28ECAEB: "Comment3",
    0xA1A929DE: "Comment4",
    0xB58D6C13: "Comment5",
    0xC9D34FEF: "Comment6",
    0xF81E70F4: "CompBonus1",
    0x03C90541: "CompBonus2",
    0x3AF333D3: "CompBonus3",
    0x8252B02B: "CompBonus4",
    0xFA2713A5: "CompBonus5",
    0xD20A0557: "Cond1",
    0x35329DDF: "Cond2",
    0x591E3B51: "Condition",
    0x3D6B02F6: "Condition1",
    0x4D3D24A1: "Condition2",
    0x8E184D75: "Condition3",
    0xE2D5DA44: "Condition4",
    0x167E711F: "Condition5",
    0xF0D6BD4D: "Condition6",
    0x9F758CA5: "ConditionParam",
    0x914E9457: "ConditionType",
    0x63080B03: "Contents1",
    0x278E0E98: "Contents2",
    0xFC693B6D: "Contents3",
    0x4617C0C5: "Contents4",
    0x22D79F12: "ContentsID",
    0xD8F6C9F7: "Continue",
    0xD9929143: "ContinueEvent",
    0xE7288A69: "ControlA",
    0x74CF9CDA: "ControlB",
    0xE57B8F53: "CookName",
    0x7E92414E: "CookRecipe",  # FIXME: unclear if correct
    0x2EC51EFC: "CookSnap",
    0x9E7D98E8: "CoolDown",
    0xB2FA4A49: "CoreNum",
    0x8871B197: "Count",
    0x0EC9D148: "Count1",
    0x54C14948: "Count2",
    0x9354C081: "Count3",
    0xC5CFB2F0: "Count4",
    0x658EF9A9: "Count5",
    0x5993CDF2: "Count6",
    0x3CA49555: "Count7",
    0x095451A3: "CountOff",
    0x40E42769: "Craft",
    0x9A42201E: "CraftBuff",
    0xA7F0D30A: "CriRate",
    0xB485E71B: "CriRate2",
    0xCF778992: "CriRev",
    0x6F83CD1F: "CurveExp",
    0x66A64921: "CurveType",
    0xA92AA9EA: "Cycle",
    0xF7CD962C: "Cylinder",

    0x83F8225F: "DLC",
    0x1E689E67: "Damage",
    0xCFB3553B: "Damage2",
    0x9E5557E6: "DamageRev",
    0x8B2BDE0F: "DamageRevHigh",
    0xCE1951BC: "DamageRevLow",
    0x85A8D5B5: "Debuff",
    0xCC2A50A4: "DebugFlag1",
    0xB6BB1396: "DebugFlag2",
    0x8238A725: "DebugID",
    0x50C06388: "DebugName",
    0x8552A9F3: "DebugName2",
    0xD2929871: "DebugName3",
    0xED7FF789: "DebugName4",
    0x5F21EE1B: "DebugName5",
    0xBD99CDB2: "DebugName6",
    0x17D57A57: "DebugName7",
    0x85998715: "DebugName8",
    0x911A2A26: "DebugName9",
    0xD4AF7D5E: "Decimal",
    0xA928A956: "Deduct",
    0xC2D519F1: "DefAcce1",
    0x121730FC: "DefAcce2",
    0x079F505B: "DefAcce3",
    0x6507A475: "DefGem1",
    0x45234126: "DefGem2",
    0xF2F1441D: "DefGem3",
    0x6590AB76: "DefHate",
    0xF3139111: "DefLv",
    0x2E11014E: "DefLvType",
    0x02C1C5DC: "DefRev",
    0xE5C59521: "DefTalent",
    0x48DB8265: "Default",
    0x976E2908: "DefaultMotion",
    0xA0CCBA9A: "DefaultOn",  # FIXME: unclear if correct
    0x555B7A5A: "DefaultResource",
    0xB50D9D10: "DescText",
    0xC3F5A67C: "Detail1",
    0x07C915FD: "Detail2",
    0xB4AF1963: "Detail3",
    0x58DE5FA5: "Detail4",
    0x288D78D1: "DetailText1",
    0xAF75D2CE: "DetailText2",
    0xAAA12595: "DetailText3",
    0x68D607C5: "DetailText4",
    0x9F7EDAF7: "DetailText5",
    0xEAA4090C: "DetailText6",
    0x48FF3C5F: "DexBase",
    0xE25262E7: "DexLv1",
    0x4ECB1F28: "DexLv99",
    0xE1E9D27F: "DexRev",
    0xD3360994: "DexRev1",
    0x5494A420: "DexRev2",
    0x6BC34A9D: "Difficulty",
    0x7E4AA0D7: "Direct",
    0x60F22C6D: "DirectFrm",
    0xF0FD1B0E: "DirectType",
    0x3F113E19: "Direction",
    0xD6C2824D: "DirectionID",
    0xC67AB331: "DirectionType",
    0x4F038590: "Dirt",
    0x899C03E4: "DirtHigh",
    0x8F57F173: "DirtLevel",  # FIXME: unclear if correct
    0x005A2321: "DirtLow",
    0xAC8AC074: "DispHeight",
    0x7DC02962: "DispRadius",
    0x756058B1: "DispTime1",
    0x4F19F286: "DispTime2",
    0x22F544BA: "DispTime3",
    0xE1232743: "DispType",
    0xE7D06056: "Distance",
    0x2804B3C6: "Dmg",
    0xFC0726EF: "DmgMgn1",
    0x6449200F: "DmgMgn2",
    0x4A3D1EF8: "DmgMgn3",
    0x49C0DEBA: "DmgMgn4",
    0xCA65D2CD: "DmgMgn5",
    0x0213C69E: "DmgRange",
    0xC23E7D15: "DmgRt01",
    0x6CE83942: "DmgRt02",
    0x5C6420B9: "DmgRt03",
    0x9C501015: "DmgRt04",
    0x7FCC39E1: "DmgRt05",
    0xBD3BE2BB: "DmgRt06",
    0xFB85BE75: "DmgRt07",
    0xDE7EF5B4: "DmgRt08",
    0x10496C8B: "DmgRt09",
    0x0D5300D5: "DmgRt10",
    0x8AF3A6CC: "DmgRt11",
    0x910F17E4: "DmgRt12",
    0xCA0E90EA: "DmgRt13",
    0x12CDF2AF: "DmgRt14",
    0x6D763CB5: "DmgRt15",
    0x49AE653A: "DmgRt16",
    0x917A91FA: "Door",
    0xCE9351B1: "DoorStatus",
    0xE5163D72: "DropProb1",
    0xAF87F02E: "DropProb2",
    0x88CFB614: "DropProb3",
    0xE74D93CD: "DropProb4",
    0xD2C56D1C: "DropProb5",
    0x8E8EA93A: "DropProb6",
    0x2C88FAA3: "DropProb7",
    0x683D7A3A: "DropProb8",
    0x69C4C06B: "DupType",
    0x061F00A3: "Duration",

    0x384A8A96: "EArmor",
    0xEF00B6DA: "EArmor1",
    0xC480EDF7: "EArmor2",
    0x9576DF93: "E_LookPosType",
    0x2774563C: "E_LookX",
    0x1721C6CD: "E_LookY",
    0x14D7A3F7: "E_LookZ",
    0x7610D4E1: "E_PosX",
    0x5C649D51: "E_PosY",
    0xD86EF467: "E_PosZ",
    0xFF814AC9: "Easy",
    0xDC18C695: "EffAtr",
    0x806E59A6: "EffID",
    0x342E6E97: "EffPack",
    0x56D033F5: "EffPack2",
    0x746716AC: "EffPack3",
    0xFFA47A48: "EffScale",
    0xBB08DA4F: "EffType",
    0xECFF4F2A: "Effect",
    0x9CEA86B5: "EffectCondition",
    0xBB44C6DD: "EffectID",
    0x025B58F7: "EffectName",
    0x02838F0C: "EffectPoint",
    0x102718E0: "EffectScale",
    0x80371DC2: "EffectStatus",
    0x234A0346: "EffectType",
    0x231EFCFC: "Efp01",
    0xE342408E: "Efp02",
    0xA08AF297: "Efp03",
    0xA5A6EEBA: "Efp04",
    0x2750FFC7: "Efp05",
    0x9C303BB1: "Efp06",
    0xF60A50D2: "Efp07",
    0x42A3D49D: "Efp08",
    0xC37C11BA: "Efp09",
    0x93CEB6AB: "Efp10",
    0xA074D190: "Efp11",
    0x2861D09B: "Efp12",
    0x32722BD1: "Efp13",
    0xFE6036F6: "Efp14",
    0xFE0446BC: "Efp15",
    0x68B80767: "Efp16",
    0x19A7ABB1: "EfpT01",
    0x5C3AB989: "EfpT02",
    0x859ECC6D: "EfpT03",
    0x525AB544: "EfpT04",
    0x73146524: "EfpT05",
    0x556AEDBF: "EfpT06",
    0x8C2DABB6: "EfpT07",
    0xA93FC1F0: "EfpT08",
    0x5AB95219: "EfpT09",
    0x10EB07AE: "EfpT10",
    0xF814ED70: "EfpT11",
    0x3B57E1F9: "EfpT12",
    0xFE5E1857: "EfpT13",
    0x29FD9511: "EfpT14",
    0x5DC76866: "EfpT15",
    0x2FE6AA46: "EfpT16",
    0x6592A95A: "EfpType",
    0x2FBC399C: "Elite1",
    0xB20997FC: "Elite2",
    0xD6C3AA7E: "Elite3",
    0xE4AEAAD7: "Elite4",
    0xEB40457F: "Elite5",
    0xF34BD15B: "Elite6",
    0xE855DE0C: "EliteScale",
    0x32984956: "EnFamily",
    0x4CA550A7: "EnSize",
    0x6029A27F: "EndAlpha",
    0x5F2088FA: "EndCheck",
    0xF1F54917: "EndCheckType",
    0x5D7ACE60: "EndFlag1",
    0xAF9F666F: "EndFlag2",
    0xB45F241C: "EndFlag3",
    0x6AA0478F: "EndFlag4",
    0x7E2A5E2B: "EndFlag5",
    0x7DB17798: "EndFlag6",
    0x815DFE9D: "EndFrm",
    0x22207986: "EndPos",
    0xC8AF01C8: "EndX",
    0xA33906FF: "EndY",
    0x6462634C: "EndZ",
    0x29210A2C: "Endf1",
    0x2665EB57: "Endf2",
    0x8AD2184D: "Endf3",
    0x611E819D: "EnemyExp",
    0xAAEA8654: "EnemyFamily",
    0x9053E074: "EnemyGold",
    0xAC3DA873: "EnemyID",
    0xB3B15FB9: "EnemyID1",
    0x426B1CB7: "EnemyID2",
    0x8E987578: "EnemyID3",
    0x03C28284: "EnemyID4",
    0xB36D05A3: "EnemyID5",
    0x8CAA1870: "EnemyID6",
    0xBD1AA5B8: "EnemyID01",
    0x7318D357: "EnemyID02",
    0x3F1ED434: "EnemyID03",
    0x516AAE38: "EnemyInfo",  # FIXME: unclear if correct
    0x0C149953: "EnemyTalentExp",
    0xBE1E9570: "Enhance",
    0x3B31AAA4: "Enhance1",
    0x5D04D2CE: "Enhance2",
    0xC4463158: "Enhance3",
    0xE71815CD: "Enhance4",
    0x660B91C9: "Enhance5",
    0xF2623BB8: "EnhanceEffect",
    0x897F2D81: "EnhanceID",
    0xCBCC6829: "EnhanceOff01",
    0x5E3262A8: "EnhanceOff02",
    0x7C1904E8: "EnhanceOff03",
    0x5A94EA41: "EnhanceOff04",
    0xD8095E96: "EnhanceOff05",
    0xF72B1441: "EnhanceOff06",
    0xBBF1449F: "EnhanceOff07",
    0x11C33AB6: "EnhanceOff08",
    0x521E9ADC: "EnhanceOff09",
    0x58EAB004: "EnhanceOff10",
    0x92EDF6CE: "EnhanceOff11",
    0xDC3916A2: "EnhanceOff12",
    0x86CD6966: "EnhanceOff13",
    0xD727886D: "EnhanceOff14",
    0x0C60AD46: "EnhanceOff15",
    0x4778DD1F: "EnhanceOff16",
    0xAF9C1F1A: "EnhanceRandom",
    0x84113B2C: "EnhanceSlot0",
    0x3E948624: "EnhanceSlot1",
    0xC9738403: "EnhanceSlot2",
    0x51954738: "EquipType",
    0x98B5A07E: "Event",
    0x5104C2B6: "EventID",
    0xEE4909E8: "EventName",
    0x13F69CCE: "EventName2",
    0x826E8B95: "EventTable",  # FIXME: unclear if correct
    0x569E4759: "EventType",
    0x77087444: "Exp",
    0x1D6A1088: "ExpBonus",
    0xA12FF282: "ExpRate",
    0x58B00160: "ExpRevHigh",
    0x2220481D: "ExpRevLow",
    0xA7197D4F: "Eye",
    0x06F82010: "EyeMotion",
    0x082F3B92: "EyeMotion1",
    0xA41DD4CC: "EyeMotion2",
    0xE1F35520: "Eyef",

    0x0DD5EF1F: "Facial",
    0x70546B59: "FadeTime",
    0x08C194FF: "FallRange",
    0xDF6378CD: "FallSpeed",
    0x701C97C7: "FamilyTag",  # FIXME: unclear if correct
    0xFBD9A20D: "FieldIcon",
    0x6F61FFC1: "FilterIndex",
    0xD2D5B25A: "FilterName",
    0x85FB836A: "FirstNamed1",
    0x18CF0753: "FirstNamed2",
    0xF9042239: "FirstNamed3",
    0xA454E525: "FirstNamed4",
    0x124FD909: "FirstNamed5",
    0x824F4279: "FirstNamed6",
    0xFF8D3677: "FirstNamed7",
    0x0BE16E27: "FirstNamed8",
    0x7E353F43: "FirstReward",
    0x6AAE1963: "FirstTry",
    0xD5700453: "Flag",
    0x687FDF50: "Flag1",
    0x870A7150: "Flag2",
    0xAC89FB66: "Flag3",
    0x1C917E7E: "Flag4",
    0xD7B5C7A8: "Flag5",
    0x4AA7B52F: "Flag6",
    0x4A4A2172: "FlagBit",
    0x972A5125: "FlagID",
    0xDA6D358F: "FlagMax",
    0xA8D0C912: "FlagMin",
    0xE5CC8125: "FlagType",
    0x33CAEB2F: "FldCond",
    0x58DF450A: "FlyHeight",
    0x8D21284B: "Focus",
    0x9FBC8DD1: "Foot",
    0x58DBEA70: "FootEffect",
    0x885D514C: "FootL00",
    0x394E89F7: "FootL01",
    0x98ECD62B: "FootL02",
    0x0E91931F: "FootR00",
    0x32DD318D: "FootR01",
    0x8A3C534C: "FootR02",
    0x654802CF: "FootStep",
    0x4F15F5FA: "Force",
    0x26FE34A4: "ForgePoint",
    0x38744A05: "ForgeType",
    0xC2EBAF3F: "FormatNo",
    0xD5FC388A: "Formation1",
    0xB450FEFB: "Formation2",
    0x4AEFCDBD: "Formation3",
    0xFC0937EB: "Formation4",
    0x41E48985: "FormationCooking",
    0xF324975C: "FormationID",
    0x5DD44D44: "FormationTraining",
    0x162DC154: "Frame",

    0x7D180799: "G",
    0xA2292967: "Gel",
    0xB93324D2: "GemLv",
    0x88059BFB: "GemSlot",
    0xB381A9C7: "Gender",
    0xA7C9DF3F: "GetNumber",  # FIXME: unclear if correct
    0x7EC6903F: "GetRatio",
    0xECEA2C59: "Gimmick",
    0xCE48890E: "GimmickID",
    0x475B17F1: "GimmickName",
    0x28D3A8B7: "GimmickType",
    0x3948DC33: "Gold",
    0xA2EA4FA8: "GoldDivide",
    0xFF7B1688: "GoldDivideRev",
    0xA80DA2A9: "GoldRate",
    0xBA987525: "GraphicsID",
    0xFF4AE68A: "Grass",
    0xD280543F: "GravOffF",
    0x5104F7F5: "GravOnF",
    0xBE21CC0C: "GraveID",
    0xDFF7A732: "Gravel",
    0xFD106EFE: "Group",
    0xBF00898F: "GroupID",
    0xC2FE2D21: "GroupName",
    0x6EC39CF7: "Grouping",
    0x421F2243: "GrowSetting",
    0x758913BA: "GuardEff",
    0x3D560F4F: "GuardRate",
    0x93553712: "GuardRate2",
    0xA40F8788: "GuardRev",

    0xFAE4E776: "HERO",
    0x6A533A4F: "Hard",
    0x037BA199: "Hate",
    0xBDCD27BC: "HateRev",
    0x05777012: "Head",
    0x7312F316: "Heal",
    0x7681AAB4: "HealRev",
    0x23A849B1: "HealType",
    0xA301E29F: "Healer",
    0x2B0F682A: "HealerProb1",
    0xB76A556E: "HealerProb2",
    0xA1E2BF1B: "HealerProb3",
    0x9AFDCD9C: "Hide",
    0x71DA17C2: "HideWeapon",
    0xD7EFBEEF: "Hip",
    0x926C6645: "HitDirID01",
    0x46852910: "HitDirID02",
    0xC31FDAAC: "HitDirID03",
    0xF215B204: "HitDirID04",
    0x22B90B35: "HitDirID05",
    0x69A41BE6: "HitDirID06",
    0xF33E0F3B: "HitDirID07",
    0x0E8101FF: "HitDirID08",
    0xA2EE3CE3: "HitDirID09",
    0xA909F155: "HitDirID10",
    0xB5F89B0E: "HitDirID11",
    0x40D22EEC: "HitDirID12",
    0x84D336C2: "HitDirID13",
    0xA1C1F15D: "HitDirID14",
    0x63BB4BD4: "HitDirID15",
    0x0D0EF9AD: "HitDirID16",
    0xCB9825CD: "HitEff",
    0x64373D45: "HitEffect",
    0xAB62281A: "HitFrm01",
    0x40A4CB10: "HitFrm02",
    0x906F4D6E: "HitFrm03",
    0x5BF6BB60: "HitFrm04",
    0xF219BB51: "HitFrm05",
    0x409663C7: "HitFrm06",
    0x7606D71E: "HitFrm07",
    0xD1DC0AB6: "HitFrm08",
    0x05A6A560: "HitFrm09",
    0xA964467F: "HitFrm10",
    0x5B68AECD: "HitFrm11",
    0xCDAFF42B: "HitFrm12",
    0x6D33E89B: "HitFrm13",
    0xE4880903: "HitFrm14",
    0x5F980BD9: "HitFrm15",
    0xE73A16C8: "HitFrm16",
    0x842EC834: "HitNum",
    0x69E82DE5: "HitRev",
    0x13F00AFE: "HitRevLow",
    0xE5CA9551: "HitSE",
    0x77058C3D: "Hitf",
    0x8EF3F61A: "HpMaxBase",
    0xF6F16AA5: "HpMaxLv1",
    0x3396A06A: "HpMaxLv99",
    0x642232EC: "HpMaxRev",
    0x86434390: "HpMaxRev2",
    0xAE6E5368: "HudIcon",

    0xDBEA0DF4: "ID",
    0x20E8CF56: "IK",
    0x7FDAC4D9: "Icon",
    0x746F48F7: "IconFlag",
    0x846CE59D: "IconIndex",
    0x6ECE0D42: "IconIndex2",
    0xFC719450: "IconNo",
    0x91274C4E: "IconOffset",
    0x17ABEC63: "IconType",
    0xA660D3E2: "IdBgm",
    0x6C228F62: "IdMove",
    0x88FA752C: "IkName",
    0x76156B2E: "ImageID",
    0x45882560: "ImageNo",
    0x5C7721C0: "ImageNo1",
    0xDD5F9B10: "ImageNo2",
    0x3E8E961A: "ImageNo3",
    0x419C0ED4: "ImageNo4",
    0x998E1DA5: "ImageNo5",
    0x8784C9EE: "ImageNo6",
    0x5CBF7E35: "ImageNum",
    0x0E35ECDD: "ImpSE",
    0x6AFEE7AF: "Impact",
    0x23B977D9: "ImpactEnhance",
    0xE70B0946: "ImpactScale",
    0x574A6DF1: "InWater",
    0xD02E4731: "Index01",
    0x452C0EAE: "Index02",
    0xE40DE564: "Influence",
    0x8F5AC8E4: "InfluenceType",
    0xCDB74611: "Info",
    0x01C46CBE: "InfoCondition",
    0xC6A4EBC9: "InfoDisp",
    0xFE37ECCA: "InfoImage",
    0x2CF1A8E3: "InfoPiece",
    0xB4B2825F: "InfoPiece1",
    0xC80006DF: "InfoPiece2",
    0x49A83CE5: "InfoPiece3",
    0x04A38848: "InfoPiece4",
    0xAD0BA31D: "InsideAlpha",
    0x6BEEE09A: "InsideScale",
    0xBA4427A4: "Intensity",
    0xD53F9B44: "Interval",
    0x295060CA: "IntervalArts",
    0x86D9BFC0: "IntervalMax",
    0x9F838917: "IntervalMin",
    0x6D294712: "Invisible_XZ",
    0x613C83D3: "Invisible_Y",
    0x1FB9379D: "Iron",
    0x6600C31F: "IsEnemy",
    0x8DF6B770: "IsGround",
    0x508AAF22: "IsLoop",
    0x0122131E: "IsPc",
    0x38F7B663: "IsTop",
    0xEBF43C80: "IsWater",
    0xE7F3EA97: "Item",
    0xDB6D9154: "Item1",
    0xA3E6E9D2: "Item2",
    0x4EFBF956: "Item3",
    0x1FB7291A: "Item4",
    0xAE48D155: "Item5",
    0x9F394AB8: "Item6",
    0x6BAC154C: "Item7",
    0x7CE39B44: "Item01",
    0x06E6253D: "Item02",
    0x6BFE9A49: "Item03",
    0x27298B32: "Item04",
    0x6D399AF9: "Item05",
    0x6263213D: "Item06",
    0x3EBEC76F: "Item07",
    0x81534641: "Item08",
    0x3953E1BA: "Item09",
    0x6EA8652E: "Item10",
    0x6913656C: "ItemCategory",
    0x26A0BB7E: "ItemCountMax",
    0x8288D449: "ItemCountMin",
    0xE9177CD3: "ItemID",
    0xBD921886: "ItemID1",
    0xFFB9B8F2: "ItemID2",
    0x3B79EAAD: "ItemID3",
    0x82C3E971: "ItemID4",
    0xE3041938: "ItemID5",
    0xF10AE7D3: "ItemID6",
    0x7BB0F65B: "ItemID7",
    0x69078E3B: "ItemID8",
    0x2219A23B: "ItemId1",
    0x05D15E4D: "ItemId2",
    0x2D76C023: "ItemId3",
    0x87F62F97: "ItemId4",
    0x181B1C36: "ItemId5",
    0x4EC6042A: "ItemId6",
    0x90467823: "ItemId7",
    0xB1813D5F: "ItemId8",
    0x1EE60CE6: "ItemId9",
    0xC7957F93: "ItemId10",
    0x963A9280: "ItemNum1",
    0xA2B85B3C: "ItemNum2",
    0xF2791823: "ItemNum3",
    0x230CF659: "ItemNum4",
    0x8B7F546C: "ItemNum5",
    0xB3C21321: "ItemNum6",
    0xD12EED4C: "ItemRate1",
    0xF1791C48: "ItemRate2",
    0xB59244EA: "ItemRate3",
    0x91189F5F: "ItemRate4",
    0x3BBC2DE9: "ItemRate5",
    0xF8F76C7F: "ItemRate6",
    0x44F549F4: "ItemRate7",
    0xEFCB767A: "ItemRate8",
    0x97CAD9C2: "ItemRate9",
    0x95989B87: "ItemRate10",

    0xA492DCCC: "Job",

    0xC253A756: "Keepf",
    0xC4B89BE5: "KevesRate",
    0x87D7DB09: "KevesReward",
    0x18F26C3A: "KeyAssign1",
    0x9EDBBA4E: "KeyAssign2",
    0xB44E6E8C: "KeyChr1",
    0x0C0273C8: "KeyChr2",
    0x40BADCBE: "KeyChr3",
    0xF65AFE60: "KeyChr4",
    0x56E97948: "KeyChr5",
    0x9F939BC6: "KeyChr6",
    0x67174E6E: "KeyShift1",
    0x9C2CAE21: "KeyShift2",
    0xD20CEFB1: "Knee",

    0xCBC5A6F6: "LandingDamage",
    0x67201E11: "LandingHeight",
    0x09AC98EA: "Leader",
    0xD7E89FF1: "Length",
    0xFBDC9172: "LevPlus",
    0x195A67F5: "Level",
    0x3CB3E68D: "Level01",
    0xAF8BBA02: "Level02",
    0x03B43464: "Level03",
    0x9D1F907A: "Level04",
    0x9F5A7530: "Level05",
    0x294AE084: "Level06",
    0xA774EC82: "Level1",
    0x401A8663: "Level2",
    0xCF81EED0: "Level3",
    0xBB0A1111: "Level4",
    0x92771993: "Level5",
    0xCDC1A2C4: "LevelExp",
    0x097B63F4: "LevelHero",
    0x0355C603: "Life",
    0x499D339B: "Link1",
    0x03B04BD5: "Link2",
    0xB1AB7B41: "Link3",
    0x6D6CF579: "Link4",
    0x9010991B: "Link5",
    0xE9EE0483: "LinkQuest",
    0xBD1B2F64: "LinkQuestTask",
    0x1E08C2CD: "LinkQuestTaskID",
    0xE4BC35A9: "Localize",
    0x78693E2C: "Localize1",
    0x86A5B309: "Localize2",
    0xB5C766E2: "Localize3",
    0xE4C6B295: "Localize4",
    0x753DFDAD: "Localize5",
    0x214001D5: "Localize6",
    0xCD7CFE78: "LocationID",
    0x32558214: "LocationName",
    0xC556517C: "Locations",
    0x28CE8A7C: "LockMsg",
    0x12E323E7: "LockType",
    0x0F649035: "LockVoice",
    0x20432698: "Lod",
    0xF9BE465A: "LookAt",
    0x0E93C20B: "LotID",
    0xC138277A: "LotRate",
    0x23F75898: "Lottery",
    0x9143A12E: "Lv",
    0x3F5C31B7: "LvMax",
    0x83CFBB4A: "LvMin",

    0x1B6CE343: "Main",
    0x441C30DF: "Map",
    0xAD11E3B6: "MapGimmickID",
    0xF96161CE: "MapID",
    0x8D5D1243: "MapJumpID",
    0xE9206287: "Marking1",
    0x7A10F206: "Marking2",
    0xE869AB5E: "Marking3",
    0x47810127: "Marking4",
    0x66E78B9A: "Marking5",
    0xE3A92C2B: "Marking6",
    0x69F8C198: "Marking7",
    0x009B610D: "MaxDelay",
    0xDF998797: "MaxHeight",
    0x2C1A0BDB: "MaxLength",
    0x84192CF4: "MaxNumber",
    0xA414E653: "MaxScale",
    0xE71EA282: "MaxShake",
    0x7DEF5DA6: "MaxValue",
    0xB1985607: "MenuCategory",  # FIXME: unclear if correct
    0x2DCB5F5B: "MenuGroup",
    0x9D56F17E: "MenuIcon",
    0xF6837482: "MenuPriority",
    0xD33A871F: "MinLength",
    0x50617ECF: "MinScale",
    0x74427D74: "Mist",
    0x3B1C6214: "Model",
    0x3F4ADAAC: "ModelName",
    0x83C071CC: "ModelName2",
    0x2972379F: "ModelType",
    0xBBE83D29: "Motion",
    0x65B4D1FC: "Motion1",
    0xF5E5DFF3: "Motion2",
    0x27BE1FCC: "Motion3",
    0xE57106AD: "Motion01",
    0xB4B30C90: "Motion02",
    0x1B0D98AB: "Motion03",
    0x56798C8E: "Motion04",
    0x9D7EE1E4: "Motion05",
    0x8167FAB8: "MotionName1",
    0x4C66D85A: "MotionName2",
    0xE47BD850: "MotionState1",
    0xEC5AE7EE: "MotionState2",
    0x365739D2: "MotionState3",
    0x06D95035: "MotionState4",
    0x9A3FF479: "MotionState5",
    0x11336F80: "MotionState6",
    0x40701959: "MotionState7",
    0x27524DED: "MotionState8",
    0x15E784A2: "MotionType",
    0xE4C3C834: "Motionf1",
    0xF64D8487: "Motionf2",
    0x05E90FEB: "Motionf3",
    0xDD591376: "Motionf4",
    0xEA404AA5: "Motionf5",
    0xA0EF60EA: "Motionf6",
    0xB3426282: "Motionf7",
    0xA1AC52B0: "Motionf8",
    0x69C00D24: "Mount",
    0xACB1E963: "Mount1",
    0x5F812FC5: "Mount2",
    0x0B9E0B95: "MountChange",  # FIXME: unclear if correct
    0x79983A13: "MountEx",
    0xB1E55BE5: "MountL",
    0xC23E4D83: "MountObj",
    0xBC55C1B6: "MountObj1",
    0x4629C370: "MountObj2",
    0x3C252BA6: "MountOut",
    0x4F6118E5: "MountPath1",
    0x9596105A: "MountPath2",
    0x1A0FFA5B: "MountPath3",
    0xEA45BD3D: "MountPath4",
    0xD207D308: "MountR",
    0x87F57F8B: "MoveBtl",
    0x89F92653: "MoveBtlRate",
    0xA85677F7: "MovePoint",  # FIXME: unclear if correct
    0xAE922AA5: "MoveRev",
    0x583DD79B: "MoveTime",
    0x01EE5797: "MoveType",
    0xB2BA00DD: "MsgID",
    0xD8DB54A1: "MsgName",
    0x463C192A: "MustRead1",
    0xD87DF2E4: "MustRead2",
    0x2B81D327: "MustRead3",
    0x9774A525: "MustRead4",
    0xBD1B8FE2: "MustRead5",
    0x3CC234F0: "MustRead6",
    0xDD069409: "MustRead7",
    0x0B5D533B: "MustRead8",
    0x971A222A: "MustRead9",
    0xC506343C: "MustRead10",
    0xB695DE79: "MutateParam",
    0x28DF3AB0: "MutateTarget",
    0x4D2721D9: "MutateType",
    0xA9F2157B: "Muzzle",
    0x4C677B43: "MuzzleScale",

    0x18F585E3: "NPC",
    0xFD1D0979: "NPCID",
    0x8017C0D9: "NPCName",
    0x2AA46552: "NPC_A",
    0x05595AB2: "NPC_B",
    0x25EFA387: "Name",
    0xD34D0587: "Name1",
    0xE07D55CB: "Name2",
    0x646C9C04: "Name3",
    0xC80CBB31: "Name4",
    0x19838CE1: "Name5",
    0xB820EB0D: "Name6",
    0x89CE063B: "NameCondition",
    0x602870A8: "NameMsg",
    0xAFCE416E: "NamedFlag",
    0xC6D66AC7: "Navi",
    0x84E8AD5A: "NeedCharacter",
    0xF8D8C576: "NeedEther",
    0xD9A8D205: "NeedGold",
    0x3BDD1BFD: "NeedRecipe",
    0x6E37CB43: "NeedSp",
    0x12D18C6A: "NextPurposeA",
    0xBAFEA17B: "NextPurposeB",
    0x76A96FE2: "Nickname",
    0x9C074FCE: "NoClear",
    0x1CD9A082: "NoSmoke",
    0x80F89F24: "NoUro",
    0x390B012D: "Normal",
    0x4A86AE4A: "Not1",
    0xD0DB2BA8: "Not2",
    0xAD30EA95: "NotQuestFlag1",
    0x62558BB2: "NotQuestFlag2",
    0xFDD1BC8B: "NotQuestFlagMax1",
    0x4A738EFE: "NotQuestFlagMax2",
    0xE5632096: "NotQuestFlagMin1",
    0x2D32BC18: "NotQuestFlagMin2",
    0xC532352F: "NotScenarioMax",
    0xF427C212: "NotScenarioMin",
    0xE204F82C: "Npc",
    0x26BDAEE5: "NpcID",
    0x2AD36178: "NpcID1",
    0x716D1B5F: "NpcID2",
    0x6D771403: "NpcID3",
    0x02C1D331: "NpcID4",
    0x42DFEFDB: "NpcID5",
    0xFAF75E90: "NpcID6",
    0x43473909: "Num01",
    0x7F13A069: "Num02",
    0xBD587404: "Num03",
    0xA8655494: "Num04",
    0x7B0CF70F: "Num05",
    0x95E58144: "Num06",
    0xE9200670: "Num07",
    0x3FC83550: "Num08",
    0x3E064AAF: "Num09",
    0x9C570EB3: "Num10",
    0x7490FDE3: "Num11",
    0x01BD7260: "Num12",
    0x783ED80D: "Num13",
    0x841D855E: "Num14",
    0xD6085712: "Num15",
    0x2D2E5A02: "Num16",
    0x02CDC73F: "Num17",
    0xAE5AFAA3: "Num18",
    0xD1539D17: "Num19",
    0x062A5799: "Num20",
    0xFE00EED8: "Num21",
    0x663B888A: "Num22",
    0x43A26A0E: "Num23",
    0x4A8747A0: "Num24",
    0xA46B8F2F: "Num25",
    0xFAA22B22: "Num26",
    0xC83B2974: "Num27",
    0xE343E418: "Num28",
    0x47FB82D2: "Num29",
    0x754714C4: "Num30",
    0xAE414048: "Num31",
    0x5A66DBEB: "Num32",
    0x751DCE18: "Num33",
    0x5E010B93: "Num34",
    0xE100E28F: "Num35",
    0xBB631E70: "Num36",
    0x47466A47: "Num37",
    0x6FED13F7: "Num38",
    0x021223CA: "Num39",
    0x208E5CA4: "Num40",
    0xF1B3147D: "Number",
    0x7D875772: "NumberMax",
    0x3E1F5D9B: "NumberMin",
    0x80163FC6: "NumberingID",

    0xBEF55022: "OFF",
    0x46D5375B: "ObjPoint1",
    0x7B0C7FE2: "ObjPoint2",
    0x6E765498: "ObjPoint3",
    0xCB1B15C5: "ObjSlot1",
    0x51AC0D3F: "ObjSlot2",
    0x065DC396: "ObjSlot3",
    0xFA8141C1: "Object",
    0xA966D9D2: "Object1",
    0x8DF017B2: "Object2",
    0x1774D63B: "Object3",
    0xD983DF25: "OffsetID",
    0x0EE249FF: "OffsetId",
    0x1F519DCB: "OffsetX",
    0x047F91FC: "OffsetY",
    0x32CF3E65: "OffsetZ",
    0x87510350: "OpenEffect",
    0xA5E65964: "OpenFlag",
    0x3A3E8378: "Option1",  # FIXME: unclear if correct
    0xF57AF32D: "OrderCondition",
    0x247A535E: "OrderIcon",
    0xD2D55B46: "OutsideAlpha",
    0x09ADE838: "OutsideScale",

    0x529B2FE3: "PArmor",
    0x1E6769F0: "PArmor1",
    0xD508BB12: "PArmor2",
    0xDB4FF313: "PC",
    0xB9AA5220: "PC01",
    0x0AE2E54E: "PC02",
    0x7041B9A4: "PC03",
    0x513A0B02: "PC04",
    0x02C41C22: "PC05",
    0xAE924C34: "PC06",
    0x49B4BB58: "PC1",
    0x505B62AF: "PC2",
    0x8C6B397A: "PCID1",
    0x75F5B631: "PCID2",
    0x433AB8D4: "PCID3",
    0xFA05A914: "PageTitle1",
    0x9A442CDC: "PageTitle2",
    0xBB40321A: "PageTitle3",
    0x9DD04BBC: "PageTitle4",
    0xB65F62BA: "PageTitle5",
    0x099C840E: "PageTitle6",
    0x2ACACD3D: "Param",
    0x24E572E6: "Param1",
    0x351C2922: "Param2",
    0xEB4CB1FE: "Param3",
    0x03E5F636: "Param4",
    0xB1ECB2CD: "Param5",
    0xBBB7D7E9: "Param6",
    0xEB0E1BFB: "Param7",
    0xDBE49DA7: "Param8",
    0xF7408AFF: "Param01",
    0x97EAB52C: "Param02",
    0xAC9CBBFC: "Param03",
    0xD078947A: "Param04",
    0x7ACF3FF2: "Param05",
    0x9F66653C: "Param06",
    0x34E1FA07: "Param07",
    0x9CEF1144: "Param08",
    0x34C8B836: "Param09",
    0xF9E1DE1D: "Param10",
    0x1E97CE3E: "Param11",
    0x7A5E69C7: "Param12",
    0x3AE18201: "Param13",
    0x5DBF4A13: "Param14",
    0x06FBB689: "Param15",
    0xB5A5AC3A: "Param16",
    0x7F574C16: "Param17",
    0x96F355A3: "Param18",
    0x3E97D37E: "Param19",
    0x0B721A3F: "Param20",
    0xD9E69402: "Param21",
    0x1F0B0AA6: "Param22",
    0x928BA5CC: "Param23",
    0x3E1B814D: "Param24",
    0x70F7D4BE: "Param25",
    0x212D3601: "Param26",
    0xE15EB634: "Param27",
    0x48D61B1A: "Param28",
    0x34AA3937: "Param29",
    0x02E2676A: "Param30",
    0xA03E9A76: "Param31",
    0x23354BF0: "Param32",
    0xBB531E33: "Param33",
    0xA2DD2D94: "Param34",
    0x24D9617D: "Param35",
    0xC5D32B91: "Param36",
    0x3DAAE9EB: "Param37",
    0xB7EE2333: "Param38",
    0x20EA357E: "Param39",
    0xABF0F9FD: "Param40",
    0x158392B3: "ParamEnd",
    0x48D0BE07: "ParamID",
    0x30A7B425: "ParamMax",
    0x6CCFF6C0: "ParamMin",
    0xA7E25CD6: "ParamStart",
    0x94FBFB5B: "PartsEye",
    0x81E7B2B8: "PartsGate",
    0xEEADBE35: "PartsId",
    0xEC5B9ED6: "PartsSwitch",
    0x1CF6B262: "PartsVisibility",
    0x3AD87FD3: "Party",
    0x22474F3E: "PartyLottery",
    0x18249A32: "PartyMax",
    0x60D0E60A: "PcID",
    0x399D4E6D: "Physical",
    0x6891830B: "Piece1",
    0xCE3A0315: "Piece2",
    0x8EFE08ED: "Piece3",
    0x5F092F34: "Piece4",
    0xF4F854BD: "Piece5",
    0xB2C52A70: "Piece6",
    0x73991E65: "Piece7",
    0x8E623B5C: "PieceID1",
    0x711DFE31: "PieceID2",
    0x7E52B9BF: "PieceID3",
    0xD40CDF66: "PieceID4",
    0xB857CB65: "PieceID5",
    0x82F1EBE5: "PieceValue",
    0xD1D96BA9: "Place",
    0xCA2E0979: "Placement",
    0xBCA71842: "Point",
    0x1F0C9E4E: "Point1",
    0xB0DF3D93: "Point2",
    0x1A3B3F17: "PointID",
    0x72F9628E: "PointType",
    0xDB2B5350: "Pop",
    0xF041F40E: "PopCount1",
    0xAA1110BE: "PopCount2",
    0x6D6A78EB: "PopCount3",
    0xCE88E2A8: "PopCount4",
    0x3F5779C7: "PopCount5",
    0xD62F315C: "PopCount6",
    0xE4CE2884: "PopEffect",
    0x7FB86D9D: "PopHeight",
    0x117AC890: "PopRange",
    0x0F482171: "PopRate1",
    0x901872DF: "PopRate2",
    0x485ACF8D: "PopRate3",
    0x90A9DAA1: "PopRate4",
    0xE8C9455F: "PopRate5",
    0x91019761: "PopRate6",
    0xA0DC3C56: "PosStatus",
    0x0029952D: "PosX",
    0x3709AF30: "PosY",
    0xCFBEAF5A: "PosZ",
    0x0C6C8102: "PowEtherLv1",
    0x1E67A8E2: "PowEtherLv99",
    0x3443EA53: "PowHealBase",
    0xA6111280: "PowHealLv1",
    0x6871BE5D: "PowHealLv99",
    0xB1A165E3: "PowHealRev",
    0x47E82470: "PowHealRev1",
    0x9A35B7A4: "PowHealRev2",
    0x65494738: "PreCombo",
    0x02A046A1: "PreCondition",
    0x4D215119: "PresetID",
    0x439CC54E: "Price",
    0xC8345C85: "Price1",
    0x47C6B94B: "Price2",
    0xBC11E5B3: "Price3",
    0x0345ECE2: "PriceCondition",
    0x170127D3: "Priority",
    0x17276C8D: "Probability01",
    0xAE0EBFAC: "Probability02",
    0x27DC69B6: "Probability03",
    0x2C495AE4: "Probability04",
    0x3835F996: "Probability05",
    0xA67AB3BC: "Probability1",
    0xFFF3AEA0: "Probability2",
    0x014F5C52: "Probability3",
    0x8970046A: "Probability4",

    0x4A7DF029: "QuestCategory",
    0xA672B4F4: "QuestFlag1",
    0xCE22BD30: "QuestFlag2",
    0xB780E0FB: "QuestFlagMax1",
    0xDF45F52F: "QuestFlagMax2",
    0x707DC974: "QuestFlagMin1",
    0x4A009760: "QuestFlagMin2",
    0xCF88D32B: "QuestID",
    0x1D15AB9C: "QuestImage",
    0x54744AEC: "QuestTalk1",
    0x649BB391: "QuestTalk2",
    0x05559F8D: "QuestTalk3",
    0x1522D323: "QuestTalk4",
    0xD7D4839A: "QuestTalk5",
    0x439AC6F1: "QuestTalk6",
    0xCA29F655: "QuestTalk7",
    0x24B46C5B: "QuestTalk8",
    0x3C433B53: "QuestTitle",

    0x79B365C1: "R",
    0xD05770A1: "RX",
    0xAA41F0C7: "RY",
    0xB9FA81E9: "RZ",
    0x49C39FA6: "Race",
    0xE7543DE7: "Radius",
    0x1E56056D: "RageCond",
    0xAA4C89F1: "RageFrm",
    0x177F1CF7: "RageInterval",
    0x5D6EE2D9: "RageParam",
    0xC57E7929: "RageStance",
    0xCA154062: "RandHero",
    0x96ACFC82: "RandPC",
    0xA05D13AD: "RandPos",
    0x9242072F: "RandRot",
    0x49FCC4E5: "RandUro",
    0xA0996C55: "Random",
    0x97B51BED: "Range",
    0xDF726F13: "RangeRev",
    0xA48A19BE: "RangeType",
    0x2647E765: "Rarity",
    0xA0EA3CD6: "ReAct01",
    0x1EA17DCD: "ReAct02",
    0xA102460E: "ReAct03",
    0xD5274EEA: "ReAct04",
    0xD2B4B40B: "ReAct05",
    0xF20FF4A1: "ReAct06",
    0x060FE530: "ReAct07",
    0xC14AEB37: "ReAct08",
    0x2B83310C: "ReAct09",
    0x46512F89: "ReAct10",
    0x47BD6B6C: "ReAct11",
    0x58C4A66C: "ReAct12",
    0x196C7308: "ReAct13",
    0xEB9ACA87: "ReAct14",
    0x714362C7: "ReAct15",
    0x1C71FF5D: "ReAct16",
    0x0D2C616E: "Reaction",
    0x35B38564: "ReactionEvent1",
    0xB2D345A0: "ReactionEvent2",
    0x30685214: "ReactionEvent3",
    0x9D6EC3C4: "ReactionEvent4",
    0x843028AD: "ReactionEvent5",
    0xA04C1F8B: "ReactionEvent6",
    0xF8CC7B2F: "Recast1",
    0x43E51C2D: "Recast2",
    0xD690DA2D: "Recast3",
    0x3BE306C1: "Recast4",
    0xC5F2D4F5: "Recast5",
    0x2E190B64: "RecastRate",
    0x328CEDF7: "RecastRev",
    0x7C372260: "RecastType",
    0x38FFA0BE: "Recipe1",
    0x2D86A7BA: "Recipe2",
    0xE48F8EFA: "Recipe3",
    0x627F3190: "Recipe4",
    0x7B9AB2FB: "ReduceEnemyHP",
    0x54C06C2D: "ReducePCHP",
    0x7AC91578: "Region",
    0xBCC81CB6: "RelationID",
    0x1E91976E: "RelationID1",
    0x9EE25CEF: "RelationID2",
    0xADD90D51: "RelationID3",
    0x5A164D3A: "RelationID4",
    0x5040CEEC: "RelationID5",
    0x75226168: "RelationID6",
    0x0D55B487: "RelationID7",
    0xDC0970C5: "RelationID8",
    0xEA65B75C: "RelationID9",
    0x2FD68965: "RelationID10",
    0xAD471ADD: "Repeat",
    0xC137BFAB: "Repeatable1",
    0x89B55973: "Repeatable2",
    0xA4AF6B3C: "Repeatable3",
    0x5BB0396F: "Repeatable4",
    0x3B7EEB90: "Repeatable5",
    0x2EBD17B3: "Repeatable6",
    0x8F2061B4: "Reply",
    0x8279E4BB: "ReplyGroup",
    0xEA2EC478: "ReplyID",
    0x44241270: "ReplyType",
    0x2CC8A5FB: "ResistCombo",
    0x1CBA1EDE: "ResistReaction",
    0xFD4F5F39: "ResistRev",
    0x6F165771: "ResistRevHigh",
    0x5BA4BC44: "Resource",
    0x75007FA0: "Resource1",
    0x4D18959A: "Resource2",
    0x4AD8D54F: "Resource3",
    0x457FDDB0: "Resource4",
    0x81D56E33: "ResourceId",
    0x498D8E22: "Respect",
    0x794B0B24: "Respect1",
    0xA5F48B16: "Respect2",
    0xFC649653: "RespectFlag",
    0x97E7543E: "RespectPoint",
    0x1D2066C9: "ResultA",
    0x16570FBD: "ResultB",
    0xD9E8B7F5: "RevGold",
    0x7FD874AD: "Reward",
    0xBEBE21A6: "Reward1",
    0x82DE85ED: "Reward1Num",
    0x1ECE883A: "Reward2",
    0x802132E0: "Reward3",
    0xAE9E7F29: "Reward4",
    0xD5C76F0A: "Reward5",
    0x8E227737: "Reward6",
    0x99180C15: "Reward7",
    0x7FC5F6E3: "Reward8",
    0xC1D0677F: "Reward9",
    0xC726C2C5: "Reward10",
    0x603E7883: "Reward11",
    0x66ECCC06: "Reward12",
    0xA410DBF6: "Reward13",
    0x913C5753: "Reward14",
    0x974017C6: "Reward15",
    0xDB288F6A: "Reward16",
    0xBECD2E94: "Reward17",
    0x4FBEB5F2: "Reward18",
    0xDCAFCE5F: "Reward19",
    0x08A14429: "Reward20",
    0xC90FB952: "RewardA1",
    0xDF864D6D: "RewardA2",
    0x0A2D9DD6: "RewardB1",
    0x61E891F2: "RewardB2",
    0xCE058792: "RewardDisp",
    0x6D90D1A3: "RewardID",
    0x58FB2440: "RewardNum1",
    0x6E002632: "RewardNum2",
    0x9E428159: "RewardNum3",
    0x645445D7: "RewardNum4",
    0xAAD0A065: "RewardNum5",
    0x8DB5D349: "RewardNum6",
    0x3F15DC43: "RewardNum7",
    0x3A4EEB50: "RewardNum8",
    0x5772A1E4: "RewardNum9",
    0x30F0F806: "RewardNum10",
    0xA2DF4624: "RewardNum11",
    0x46E430CC: "RewardNum12",
    0xC902365B: "RewardNum13",
    0x00B46D7E: "RewardNum14",
    0x65179D26: "RewardNum15",
    0xD6960383: "RewardNum16",
    0x9E9C9FCF: "RewardNum17",
    0x47D6E659: "RewardNum18",
    0xB475D1C7: "RewardNum19",
    0x41F45B76: "RewardNum20",
    0x81F47B72: "RewardSetA",
    0xFA8499A0: "RewardSetB",
    0x189340C2: "RewordID",
    0x1FE3CF92: "RewordName",
    0x3BA43A7F: "RewordText",
    0x0651F8B8: "Role",
    0x05F54B3F: "Role1",
    0x5B5CEBE7: "Role2",
    0x4AAF80EF: "Role3",
    0x641767C7: "RoleActOff01",
    0x7432058D: "RoleActOff02",
    0xD3F9860D: "RoleActOff03",
    0x9AE8A9A0: "RoleActOff04",
    0xFF757B22: "RoleActOff05",
    0x9B2F6319: "RoleActOff06",
    0x85BC475E: "RoleActOff07",
    0x85DCA26A: "RoleActOff08",
    0xE1CEA0AB: "RoleActOff09",
    0x84CA9BF5: "RoleActOff10",
    0x8C3367F7: "RoleActOff11",
    0x49E831DF: "RoleActOff12",
    0xEF5596D7: "RoleActOff13",
    0x4B4E7048: "RoleActOff14",
    0x3107F342: "RoleActOff15",
    0x9C9A37EF: "RoleActOff16",
    0x50A4664B: "RoleParam1",
    0x1F2865DB: "RoleParam2",
    0xF5C790AA: "RoleTag",
    0xEB12D0C5: "RotX",
    0x62DE4328: "RotY",
    0xF8E985AE: "RotZ",
    0x8B7A777F: "RowName",
    0xD2095834: "RowType",
    0x2D5DFFE9: "RscPreset",
    0xBB354466: "RscType",
    0x5AB6C412: "Run",

    0x0F379CF9: "SE",
    0x95AB71D2: "SEType",
    0xD5CF47B4: "SORT",
    0x03F4193A: "SP",
    0xD3D11B9E: "SX",
    0x2B4D1ECE: "SY",
    0xC847AF18: "SZ",
    0x719305F9: "S_LookPosType",
    0x2AF4EC38: "S_LookX",
    0x3E387C39: "S_LookY",
    0xDCD67D12: "S_LookZ",
    0x4B23F9CD: "S_PosX",
    0xBC7501DB: "S_PosY",
    0x5D0DB3C5: "S_PosZ",
    0x122A7D23: "Sand",
    0x6B1EAF3C: "Scale",
    0x9E1C3ACD: "Scale1",
    0xB6FB4153: "Scale2",
    0xB0FE0D4C: "Scale3",
    0xD0B66101: "Scale4",
    0xFB06A700: "Scale5",
    0x404B5078: "Scale6",
    0x4F1D90A0: "Scale7",
    0x57911F24: "ScaleHigh",
    0xDFBD827A: "ScaleHigh1",
    0x156936CA: "ScaleHigh2",
    0x1FAE0E4B: "ScaleHigh3",
    0x1FE06C3B: "ScaleHigh4",
    0x69BFB0EE: "ScaleHigh5",
    0x8C69AC10: "ScaleHigh6",
    0x086A0564: "ScaleHigh7",
    0x6887B378: "ScaleHigh8",
    0xD22CD747: "ScaleHigh9",
    0xA21C8A41: "ScaleHigh10",
    0xC6B8D75B: "ScaleHigh11",
    0xB330974D: "ScaleHigh12",
    0x0D6AF9EC: "ScaleHigh13",
    0x1D934641: "ScaleHigh14",
    0xE90811E5: "ScaleHigh15",
    0xAF8EE8A1: "ScaleHigh16",
    0xD83068DF: "ScaleLow",
    0xB0E6DC5D: "ScaleLow1",
    0xBAC53610: "ScaleLow2",
    0x93FDBC8F: "ScaleLow3",
    0x4341E911: "ScaleLow4",
    0x3870D6F1: "ScaleLow5",
    0x30E3FC75: "ScaleLow6",
    0xEAA9A7E2: "ScaleLow7",
    0x87CA2760: "ScaleLow8",
    0x7DB01867: "ScaleLow9",
    0x19E7EE6C: "ScaleLow10",
    0x764A864A: "ScaleLow11",
    0xD3629DC8: "ScaleLow12",
    0xECB07663: "ScaleLow13",
    0x04159EB1: "ScaleLow14",
    0x38AADBED: "ScaleLow15",
    0xED50D34A: "ScaleLow16",
    0x883A98D0: "ScaleMax",
    0x504B0912: "ScaleMin",
    0x94AD00AA: "ScalePlus",
    0xE75E2DBA: "ScaleTime",
    0x4EE71A4F: "ScaleX",
    0x0BCE334D: "ScaleY",
    0xBF03DA5F: "ScenarioCond",
    0xCEFBB4DD: "ScenarioFlag",
    0x85A5428D: "ScenarioMax",
    0x859DC111: "ScenarioMin",
    0x7877BAA8: "Script",
    0x6BB6B20E: "Se",
    0x392AE7B6: "SeCondition",
    0x064F807E: "SeName",
    0x97D8A256: "SeRange",
    0x02EF6156: "Sell",
    0x61EB3803: "SequentialID",
    0xDC6907B2: "SetAnim",
    0x4B01A7A2: "SetItem1",
    0x7C77D821: "SetItem2",
    0xDDCCF720: "SetItem3",
    0x04473917: "SetItem4",
    0xD6B61845: "SetItem5",
    0x09F65D30: "SetItem6",
    0x607FACD4: "SetItem7",
    0xACCE04F4: "SetItem8",
    0xF44E371E: "SetItem9",
    0x6FE92D9C: "SetItem10",
    0xA703DDB8: "SetName",
    0xFDE509B1: "Sex",
    0x32015D22: "Shallows",
    0xE0D1DACE: "Shape",
    0x895919DB: "ShipStart",
    0x00825588: "ShopCondition",
    0xB4BC8DE9: "ShopID",
    0x63FD813D: "ShopItem1",
    0x64DF6E33: "ShopItem2",
    0x3882D46E: "ShopItem3",
    0xFD26E5D7: "ShopItem4",
    0xEED382ED: "ShopItem5",
    0x4A64B927: "ShopItem6",
    0xC1BFB681: "ShopItem7",
    0xA326BFBA: "ShopItem8",
    0xC4E7AB3B: "ShopItem9",
    0xD364486B: "ShopItem10",
    0x8469C864: "ShopItem11",
    0x4B3F2A74: "ShopItem12",
    0x41212731: "ShopItem13",
    0x5D42F6EE: "ShopItem14",
    0xA4E81D59: "ShopItem15",
    0xAB0F32AE: "ShopItem16",
    0xBBE3D81C: "ShopItem17",
    0x4A82CE6A: "ShopItem18",
    0x7AE725C0: "ShopItem19",
    0xD07C6A2B: "ShopItem20",
    0x791D87C4: "ShopType",
    0xB4A58247: "Size",
    0x3AB04412: "Skill1",
    0x4B2A54B0: "Skill2",
    0x5CC9E462: "Skill3",
    0x218BC28B: "Skill4",
    0x6A98F183: "Skill5",
    0x7E7DFE51: "Skill6",
    0x9534FCC4: "SkillID",
    0xC9DB78A2: "Slide",
    0xFBE02251: "Slow",
    0x0B1F1399: "SlowDirection01",
    0x3E4C4EB3: "SlowDirection02",
    0x41822361: "SlowDirection03",
    0xBD20771D: "SlowDirection04",
    0x923621A1: "SlowDirection05",
    0x121B9D00: "SlowDirection06",
    0x2195598E: "SlowDirection07",
    0x11E468E0: "SlowRate1",
    0xD5CEE2CF: "SlowRate2",
    0xF0D7266F: "SlowRate3",
    0x58122AA1: "Slowf",
    0x47F627BD: "Snow",
    0x9999D173: "Soil",
    0xE642E3E3: "SortCategory",
    0x632C239C: "SortID",
    0x3ACA445C: "SortNo",
    0x55914E09: "SortParam",
    0x07003D62: "Sound",
    0xF87E01F8: "Soup",  # FIXME: unclear if correct
    0xFADD8F74: "SpBattle",
    0x36D44960: "SpMax",
    0x8AFDD2DD: "SpMax1",
    0xCF1E9F7B: "SpMax2",
    0x56182AE2: "SpModel1",
    0x407DF9B9: "SpModel2",
    0xB686C397: "SpProb",
    0x86A4CB86: "SpRecast1",
    0x825B4F1E: "SpRecast2",
    0x8CDDAF6A: "SpScale",
    0xA7CD2D9C: "SpdFirst",
    0x7BE896BE: "SpdLast",
    0x96DD913C: "Special",
    0x233C57C0: "SpeedNum",
    0x66D79648: "SpeedType",
    0x94EDD353: "Spine",
    0xE3A6916E: "Spine0",
    0x0A5BE075: "Spine1",
    0x54ADA678: "Spot",
    0x976A02FB: "SpotGimmick",  # FIXME: unclear if correct
    0xA907267C: "SpotName",
    0xA9C89843: "Stability",
    0x434EDE03: "Stance",
    0x999DB1DD: "Stance1",
    0xC80C3A64: "Stance2",
    0xC5EE0BC7: "Stance3",
    0x29B802BC: "Stance4",
    0x5CA0A161: "Stance5",
    0x8A593227: "Start",
    0x9B9C468C: "StartAlpha",
    0xE3E3E422: "StartEvent1",
    0xDAD497F9: "StartEvent2",
    0x84036C88: "StartEvent3",
    0x0681060A: "StartEvent4",
    0x6AB64516: "StartEvent5",
    0x38649888: "StartEvent6",
    0xAD4D05BC: "StartOffset",
    0x99414D7C: "StartPos",
    0x0EF211C4: "StartPurpose",
    0xED9877CC: "StartX",
    0xD699611A: "StartY",
    0x770DC462: "StartZ",
    0x8B06CB0B: "Startf1",
    0x00F45CBA: "Startf2",
    0x70C10A38: "Startf3",
    0x95CAA187: "StateName",
    0x35BA8008: "StateName1",
    0x06069715: "StateName2",
    0xA3A624FE: "StateName3",
    0xB816AB04: "StateSave",
    0x8A62C34B: "StateVisible",
    0x68AC0E24: "Status",
    0xFFF2AC50: "StatusSave",
    0xC4CAB060: "StatusType",
    0x4F8C0DAC: "StepOffset",
    0x2CF4E695: "StepOffset1",
    0xC9025CE4: "StepOffset2",
    0x17EE0B02: "StepOffset3",
    0x3302CEDB: "StepOffset4",
    0x7FEB0F45: "Still",
    0xF2FA453F: "StoryID",
    0x866B049F: "StoryRsc",
    0x42D40247: "StoryTitle",
    0x0D26564D: "StrengthBase",
    0x0A4C0921: "StrengthLv1",
    0xAF61119D: "StrengthLv99",
    0x9B8848C8: "StrengthRev",
    0xCCCC2D9C: "StrengthRev1",
    0xE8884FA1: "StrengthRev2",
    0x7379AC7F: "SubType",
    0x9D381CE4: "Subtitling",
    0xA3A34068: "Summary",
    0xB6117BD8: "SummonType",
    0xB06CD4E4: "Swim",
    0xCC8F678E: "SwimHeight",
    0x7FBFAF1A: "SwitchModel1",
    0x82755518: "SwitchModel2",
    0x51D9E79B: "SwitchModel3",
    0x86A72E32: "SwitchModel4",
    0xD93E2CA9: "SwitchParts1",
    0x747C209F: "SwitchParts2",
    0xD95AAFC0: "SwitchParts3",

    0x168F9AFE: "TableID",
    0xFC21A92C: "Talent",
    0xD326AFD0: "Talent01",
    0x7E87EF71: "Talent02",
    0xEEE97274: "Talent03",
    0x8BBB0C3C: "Talent04",
    0xEF5EB96E: "Talent05",
    0xEBBF8659: "Talent06",
    0x46B954CF: "Talent07",
    0x1B9CEFF5: "Talent08",
    0xF85C8B4C: "Talent09",
    0xD2CE7D90: "Talent10",
    0xC1FB0B16: "Talent11",
    0x7151A777: "Talent12",
    0x8A11AA8F: "Talent13",
    0x34437200: "Talent14",
    0x4281B85B: "Talent15",
    0x7632CDFC: "Talent16",
    0x8FDB5A65: "Talent17",
    0xA0EF49B5: "Talent18",
    0x9068B428: "Talent19",
    0x52D2B9DC: "Talent20",
    0xFE0DB1CF: "Talent21",
    0x1B8939CE: "Talent22",
    0xA462E968: "Talent23",
    0x60DAB41B: "Talent24",
    0x8AEE675E: "Talent25",
    0x5ABD2128: "Talent26",
    0x40169925: "Talent27",
    0xD08BF63C: "Talent28",
    0x08A6C320: "Talent29",
    0x204F10FE: "Talent30",
    0xA6C392B9: "Talent31",
    0xE9ABDF09: "TalentAptitude1",
    0x54828F99: "TalentAptitude2",
    0x6D7E8238: "TalentAptitude3",
    0x1C824A93: "TalentAptitude4",
    0xC47B45C5: "TalentAptitude5",
    0x36E2F29F: "TalentAptitude6",
    0x9D86BEB0: "TalentArts1",
    0xC172A926: "TalentArts2",
    0x8679DD2A: "TalentArts3",
    0xF6BAD063: "TalentExpRevHigh",
    0x18C4BBE3: "TalentExpRevLow",
    0x9EB18DE8: "TalentID",
    0xC8FC78C0: "TalkCategory",
    0x3D4FED0F: "TalkID1",
    0x09A3CD53: "TalkID2",
    0x9A67BA94: "TalkID3",
    0x8C9FB525: "TalkID4",
    0xA9C1AADF: "TalkID5",
    0x30167069: "Talker",
    0x33BFB952: "Tank",
    0x1226410C: "TankAtk",
    0xA4782466: "TankHeal",
    0x7D4843D2: "TankProb1",
    0x36C93922: "TankProb2",
    0xD4874F5E: "TankProb3",
    0x6606341D: "Target",
    0x2A2BB324: "TargetFile",
    0x07C4E712: "TargetID",
    0xDB3DB43B: "TargetID1",
    0xBBD02B7D: "TargetID2",
    0x0892984B: "TargetID3",
    0x7CC8F962: "TargetID4",
    0x6CEBD417: "TargetID5",
    0x6E0433EC: "TargetID6",
    0x807D07E6: "TargetID7",
    0x6AE942F6: "TargetID8",
    0xF7F757F6: "TargetMob1",
    0x1A42CC6C: "TargetMob2",
    0xA7E9EDCA: "TargetMob3",
    0x4B5F28FA: "TargetParam1",
    0x7E346A4A: "TargetParam2",
    0xB880AA39: "TargetRole1",
    0x0ED477D5: "TargetRole2",
    0xEB9CBDA8: "TaskFlag1",
    0xB1D5132A: "TaskFlag2",
    0xC9196709: "TaskFlag3",
    0x87614528: "TaskFlag4",
    0x957BD833: "TaskID",
    0x0DA8928F: "TaskID1",
    0xA8909895: "TaskID2",
    0xC7D48915: "TaskID3",
    0xA71219C7: "TaskID4",
    0xF6035A35: "TaskLog1",
    0xCBE408D8: "TaskLog2",
    0x8227D03B: "TaskLog3",
    0x7F3C23A3: "TaskLog4",
    0x123F673C: "TaskType1",
    0x8D8A63C2: "TaskType2",
    0x0F13EFD8: "TaskType3",
    0x6F1531D7: "TaskType4",
    0x26A5DA94: "TensionUp",
    0xD0569933: "Text",
    0x116DDB79: "Text1",
    0x7944C3C4: "Text2",
    0xBBD32B85: "Text3",
    0xC151A414: "Text4",
    0x35B1870E: "Text5",
    0x78261946: "Thumbnail",
    0xAA1F82B8: "Time",
    0x49F379CB: "Time1",
    0x0A21854F: "Time2",
    0x4C8B7AF6: "Time3",
    0x9266C12D: "Time4",
    0xC26F9BA0: "Time5",
    0xB3FC2791: "TimeMax",
    0xC71B9C7B: "TimeMin",
    0xA05A9E6A: "TimeRev",
    0x87AC63D7: "TimeStop",
    0xB628287F: "TimeZone",
    0x1AB59777: "TimeZone01",
    0x5824F394: "TimeZone02",
    0xF5DBBC70: "TimeZone03",
    0xB869FE1B: "TimeZone04",
    0x92B324A2: "TimeZone05",
    0x96B61896: "Tips1",
    0x30966EE4: "Tips2",
    0x3D3B905C: "Tips3",
    0xCD68534A: "Tips4",
    0x83C826A9: "Tips5",
    0x43080996: "Title",
    0x8D21DDD0: "TitleText",
    0x4B10B0AE: "Toe",
    0xCDFE0FFF: "ToonID",  # FIXME: unclear if correct
    0x7BB929C1: "Turn",
    0x90AABEC0: "TurnAngle",
    0x30D7C462: "TurnSize",
    0x276AEEEC: "Tutorial",
    0xCCBCA061: "TutorialID",
    0x52FFF41A: "TwinBonus",
    0x289E9D69: "TwinEff",
    0x92E9CCC6: "TwinRadius",
    0x746585E5: "Type",
    0x0E12CEBC: "Type1",
    0x02A535A3: "Type2",
    0xA5CBCF01: "Type3",
    0x6BB963B0: "Type01",
    0x563578ED: "Type02",
    0xA1F8EFBF: "Type03",
    0xECFACBE7: "Type04",
    0xDAD1F9E3: "Type05",
    0x3D4BF747: "Type06",
    0x95002248: "Type07",
    0x4AB12A6A: "Type08",
    0x59E5A38A: "Type09",
    0xB656F23E: "Type10",
    0x714A641F: "Type11",
    0xE18446F1: "Type12",
    0xB1EE725E: "Type13",
    0x69F9DAD1: "Type14",
    0xF792E70E: "Type15",
    0xC81E23D9: "Type16",
    0x88F2F00C: "Type17",
    0xEE4AF5CE: "Type18",
    0xDA46D05B: "Type19",
    0xFCF71C91: "Type20",
    0x05F86DFD: "Type21",
    0x35369E90: "Type22",
    0xEF102A35: "Type23",
    0xE1907DBF: "Type24",
    0xF3C3C04F: "Type25",
    0xEFE3CC72: "Type26",
    0xFB0E6E32: "Type27",
    0x02778F8A: "Type28",
    0x708381F2: "Type29",
    0x8DD43E77: "Type30",
    0x865B49DE: "Type31",
    0x4B31A8E7: "Type32",
    0x1FA1FD92: "Type33",
    0x53245723: "Type34",
    0x64EB71F8: "Type35",
    0x904ECDCD: "Type36",
    0x8F57AA6A: "Type37",
    0x45FED8AA: "Type38",
    0xAA5E670A: "Type39",
    0xBBDEC830: "Type40",

    0x1E43B8B1: "UIX",
    0xE21937B8: "UIY",
    0x32FC4F37: "Ultimate",
    0xFA8A1282: "Unique",
    0xB7A36E4D: "UniqueDirection",
    0x9146D0A4: "UnitText",
    0x60C02D92: "UpSpeed",
    0x91F2B0B9: "UroBody",
    0xEB9A43BB: "UroBodyID",
    0xED24DD29: "UroCondition",
    0x0B61396C: "UroID",
    0x5670FDDD: "UroProb1",
    0xF1D17644: "UroProb2",
    0x497CAEFC: "UroProb3",
    0x0C35E68D: "UseChr",
    0x5E97EC7D: "UseHP",
    0xA0AB85B5: "UseTalent",
    0x5DBC6429: "UseUro",

    0x37FDFB36: "Value1",
    0x0691DD47: "Value2",
    0xCB6E1BC4: "Value3",
    0x4915BE91: "Value4",
    0x1DE2CC4F: "Value5",
    0x09F4A7C0: "Value6",
    0x6961ED8C: "Value7",
    0x2100DCBE: "Value8",
    0xB4075796: "Value9",
    0xB7E98E9C: "Value10",
    0xCB5ECEBC: "Value11",
    0xB7C2936B: "Value12",
    0xAF4AA97F: "Value13",
    0x2D6075C8: "Value14",
    0x45810042: "Value15",
    0x5F05AD4D: "Value16",
    0xAE3CC735: "Value17",
    0x3CEEE1F1: "Value18",
    0x1436F7D8: "Value19",
    0xF9AADF26: "Value20",
    0xA3115C7A: "ValueOffset",
    0x1BF4A556: "VanishParam1",
    0xE06543AD: "VanishParam2",
    0xFBB7BD7D: "VanishType",
    0x9ED38DD0: "Vibration",
    0x62249FF3: "Vignette01",
    0xBA29FC35: "Vignette02",
    0x26561182: "Visible",
    0xCD032208: "Visible1",
    0x6D24658E: "Visible2",
    0x8BABE33C: "Visible3",
    0xB151DE3B: "Visible4",
    0x32B9AC73: "VisibleMain",
    0x42E3622D: "Visible_XZ",
    0xE45C4632: "Visible_Y",
    0x53796CC2: "VoGroup",
    0x456117B6: "Voice",
    0x1BB63774: "Voice1",
    0x792B3E42: "Voice2",
    0x6D86E8EE: "Voice3",
    0x2C510418: "Voice4",
    0x90A9B175: "Voice5",
    0x721DCD1A: "Voice6",
    0x89A964F0: "Voice7",
    0xEFDEBDD3: "Voice8",
    0x3F59713B: "VoiceDead",
    0x9A0229F5: "VoiceID",
    0x56B66C27: "VoiceID1",
    0x5B64D43D: "VoiceID2",
    0x2A29B7C0: "VoiceID3",
    0x6BE6F227: "VoiceID4",
    0xA205DD28: "VoiceID5",
    0xA40FFBDD: "VoiceProb",
    0x6C9EF00E: "VoiceRand",
    0x64C95543: "VoiceType",
    0x2281C055: "VoiceUnique",
    0x30721499: "VolID",

    0x478F97FE: "WaitEnd",
    0x4F12D691: "WaitTime",
    0x14561F4A: "Waitf",
    0x73A88931: "Walk",
    0xD21B65B6: "Water",
    0xF4CB3858: "WaveFreq",
    0xD8A3A4C9: "WaveRandom",
    0x51F76591: "WaveRate",
    0x10D576D2: "WeaponA",
    0x8D616699: "WeaponB",
    0x443D49FA: "WeaponC",
    0x3B2A172F: "WeaponName",
    0x4D4DBEF8: "WeaponScale",
    0x7E73BAEA: "WeaponType",
    0x8516998C: "WeaponType2",
    0x382789E1: "Weather",
    0x33FF3E81: "Weather1",
    0xA219D0C0: "Weather2",
    0x40F7BFE9: "Weather3",
    0x0F680A3E: "Weather4",
    0x34A75CAD: "WeatherName",
    0x9FF8C60A: "WeatherRate1",
    0x8D3FF459: "WeatherRate2",
    0x2CEE5731: "WeatherRate3",
    0xC24F931E: "WeatherRate4",
    0xFF43DC29: "WeatheringRate",
    0x36CEE6A8: "Weight1",
    0xFD2FBE01: "Weight2",
    0xCF28837A: "Weight3",
    0x4119C6D0: "Weight4",
    0xA6CC631A: "Weight5",
    0x9E9470FB: "Weight6",
    0x85727543: "Weight7",
    0xD6D48DE9: "Weight8",
    0x6B31F48D: "Weight9",
    0xFB8C5E29: "Weight10",
    0xF333A7F3: "Weight11",
    0xAADBDB9D: "Weight12",
    0x7B361F5A: "Weight13",
    0x5AE900BA: "Weight14",
    0xB4C69537: "Weight15",
    0x36FC4C34: "Weight16",
    0x12EBC330: "WhiteAddRate",
    0xEB213538: "Wood",
    0xA4068AA7: "WpnParam",
    0x83E79816: "WpnType",

    0x2814D70C: "X",
    0x900BB2F8: "XOffset",

    0xDD29F651: "Y",
    0xF251385E: "YOffset",
    0x472C07CB: "YSnap",

    0x3DBAC09D: "Z",
    0xEBC9DC01: "ZOffset",
    0x0860151E: "Zone",

    0xDCB1D1CC: "act_hash",
    0xE06D0EBD: "actionTime1",
    0x8B399357: "actionTime2",
    0xEA937F24: "actionTime3",
    0xE98E1076: "actionTime4",
    0x828EC87D: "action_name",
    0x5B6EAFC0: "affName",
    0x4C213412: "affType",
    0x12499476: "align_h",
    0x9E9E52F3: "arts01",
    0x62060484: "arts02",
    0x8517E9BC: "arts03",
    0x6890CA45: "arts04",
    0x27778B9D: "arts05",
    0x99B18FCB: "arts06",
    0x641A2810: "assign",
    0x237F2209: "autoFocus",

    0xC512A4D6: "bgmEnd",
    0x65DCA094: "bgmStart",
    0xBCEA9336: "blend",
    0x950ED819: "bone_name",

    0x42146B30: "cache",
    0x95D1518E: "cam_angle",
    0xA8C2FF93: "cam_lx",
    0x2FF4F0CB: "cam_ly",
    0x930A1C7E: "cam_lz",
    0xE83EEBC1: "cancel_key",
    0xDF5E5B3A: "cancel_sound_id",
    0xE5D49F78: "cat_id",
    0x574B5FBE: "category",
    0xE06B8B51: "category_type",
    0xC9299D94: "chapter",
    0x304AA2DE: "clockHour",
    0xEB14AC98: "clockMinute",
    0x1E25EA3C: "clockStop",
    0xC37DBA8D: "coin_rate",
    0xD1152E31: "colFilterFar",
    0x8BC7F50B: "colFilterNear",
    0x3B1B8BC3: "collection_rate",
    0x9FA9624D: "comment",
    0x55C2192F: "cond_location",
    0x8CD113AF: "condition",
    0x978FD389: "condition2",
    0xF34ECD53: "condition3",
    0x6EE6BBBF: "condition4",
    0xF363CBB5: "condition5",
    0xFA6475EF: "conf_type",
    0x8AD91A82: "conf_value",
    0x7FB8BB25: "contents_id",
    0xF01AE6F7: "control_type",
    0xB647CCBF: "costume",
    0x48B25DC7: "cssnd",
    0xF18AED3E: "cut",

    0x006262B7: "data[0]",
    0x29AF5FD1: "data[10]",
    0x7DC722E5: "data[11]",
    0x1A677824: "data[12]",
    0x3CC1E4BE: "data[13]",
    0x62811835: "data[14]",
    0x06D78ECA: "data[15]",
    0x59427A13: "data[16]",
    0x80958FAF: "data[17]",
    0xE6C48DB6: "data[18]",
    0x1E54ADD5: "data[19]",
    0xAF79AEF6: "data[1]",
    0x225221C5: "data[2]",
    0x0BB9EA34: "data[3]",
    0x03CD0317: "data[4]",
    0x1B63D6E0: "data[5]",
    0x83BAD1B0: "data[6]",
    0xB3B1038A: "data[7]",
    0x81F1BE34: "data[8]",
    0x6008EC4A: "data[9]",
    0xA8C7630A: "debugName",
    0x2F78C883: "defaultAnim",
    0x59928D37: "defaultEquip",
    0x8ED2CF0D: "default_index",
    0x7037E986: "default_text",
    0xC87317A1: "default_value",
    0x2A7CCEAA: "dispParts",
    0x2EEA20E7: "disp_check",
    0x6A010A24: "disp_range",
    0x5EBFB0FB: "disp_name",
    0x472A115E: "dist",

    0x819995FF: "edFadeColB",
    0x86EBDA22: "edFadeColG",
    0xEE2E7FFB: "edFadeColR",
    0x7358EE77: "edFadeIn",
    0x2AF187F9: "edFadeInEnable",
    0x95616F1D: "edFadeOut",
    0xD097B87B: "edFadeOutEnable",
    0x3FB6088A: "edFadeWait",
    0xB02B2502: "eff_col",  # FIXME: unclear if correct
    0x9DD4688B: "enableNopon",
    0x2E0D780B: "endID",
    0x043495C0: "equip01",
    0x9D058535: "equip02",
    0x51B6A66B: "equip03",
    0xDD03CC80: "equip04",
    0x2C807050: "equip05",
    0x13D7F5BE: "equip06",
    0x69CDDAC8: "equip07",
    0x3B865B38: "equip08",
    0xC8F98F02: "equip09",
    0x6F047DD8: "equip10",
    0x26D2DEAD: "equip11",
    0x6C2E7BB7: "equip12",
    0x46B4AFA7: "equip13",
    0x5D42564D: "equip14",
    0xCD5E4889: "equip15",
    0x04EEE727: "equip16",
    0xE0530F09: "equip17",
    0xC7775B33: "equip18",
    0x95287327: "equip19",
    0x9ABA8946: "equip20",
    0x0A1B1D10: "equip21",
    0x353EBF8D: "equip22",
    0xC7D5A2E9: "equip23",
    0xAF631083: "equip24",
    0xAFB7ABF8: "equip25",
    0x2D342EE1: "equip26",
    0x32EC3D57: "equip27",
    0x6D3C3964: "equip28",
    0x67A42037: "equip29",
    0x889F05BC: "equip30",
    0xE0FAAB9D: "equip31",
    0x5F1D4572: "ev01_id",
    0xDE23162C: "ev02_id",
    0x8909EC49: "ev03_id",
    0x842235B6: "ev04_id",
    0xFC515E71: "ev05_id",
    0x611215D0: "ev06_id",
    0xCAFFC855: "ev07_id",
    0x6860F6F1: "ev08_id",
    0x520F0689: "ev09_id",
    0x608BC1BE: "ev10_id",
    0x90C0C7F8: "event",
    0x4B5D6B16: "eyePatch",

    0x2B64883B: "f",
    0x8EABE9FB: "far_val",
    0x1A11B2B3: "file",
    0xAE33C36B: "file_name",
    0x199D68D3: "filename",
    0xF84C1C24: "filter_type",
    0xBDFE08D4: "filter_value",
    0x9302D2B4: "fixed_equip",
    0x26B65FC0: "fixed_time",
    0xB04EE1B4: "fixed_weather",
    0x8DB4C2B0: "foMin",

    0xC309B74D: "gainHigh",
    0xF21B5BEF: "gainLow",
    0x34CC74A5: "getflag",
    0xF0666ADD: "gold",
    0x3CDE1626: "group",

    0xF591F3D9: "hair_change",
    0xAC615EDC: "help",
    0xED364084: "help1",
    0xDAFC4042: "help2",
    0x0E93EC2B: "help3",
    0x80AD550E: "help4",
    0x82CE30B4: "hero",
    0x5FE020E3: "hideEne",
    0x1428C378: "hideList",
    0xE041ECEB: "hideMap",
    0xD85A9394: "hideMob",
    0xF91C68D2: "hideNPC",
    0x7CB7A7E0: "hideNpc",
    0x25C830D9: "hideWpn",
    0x4E2FFF67: "hint",
    0xC09EB8CC: "hlv",

    0x76DDA449: "icon_index",
    0x19C8662E: "image_no",
    0xF0929986: "image_type",
    0x077F34F0: "index",
    0xE22D9C0E: "influence",
    0x91B22EFE: "item",

    0x7419620C: "job",

    0x3485A9CB: "key_block",

    0x8C7DD24D: "label",
    0xC1DD59A5: "leader",
    0x4377228A: "lens",
    0x2E5761D4: "level_name",
    0x7AFAE3E0: "level_name2",
    0x1F4510F2: "level_name3",
    0xF5261447: "level_name4",
    0x411AE120: "level_name5",
    0x7EF6196C: "level_priority",
    0x70A98C21: "linkCondition",
    0xA659C879: "linkCondition2",
    0xB2269620: "linkID",
    0xE7FEEB1D: "linkID2",
    0x42B39C83: "listenType",
    0x0D84CC38: "listenX",
    0x0089B570: "listenY",
    0xB3E36E9E: "listenZ",
    0x92337F61: "locationEvent",
    0xE44E70AF: "loop",
    0xB25B017B: "loopInterval",

    0xEB1D32C8: "map",
    0x0A944247: "mapID",
    0x19A5205D: "mask_color",
    0xF764370B: "max_value",
    0x64282B04: "menu_command",
    0x0B146E5F: "menu_value",
    0x1B9FFA78: "min_value",
    0xFC144A3D: "mioHair",
    0x4CB13E78: "modelDirection",
    0x3FD3BE67: "modelName",
    0xDDA1799F: "modelType",
    0x4722094E: "motionArts00",
    0x5DF4C130: "motionArts01",
    0x8782DEE6: "motionArts02",
    0xA344E560: "motionBattle",
    0x5DAA5FE5: "motionEvent",
    0xCE804A44: "motionField",
    0x4BFDC85B: "motionWeapon",
    0x278376C1: "mountObj",
    0x265958E0: "mountTag",
    0x762332A8: "mountTag2",
    0xA5AA8DD4: "mstxt",

    0xDBAF43F0: "name",
    0x62D50195: "name1",
    0x2C1E8D9B: "name2",
    0x92E424B8: "name3",
    0x551EC19E: "name4",
    0x4C2F68E0: "name5",
    0x942FA1D0: "name6",
    0xB3A41082: "name7",
    0x8555E4CE: "name8",
    0xD1B9EBF4: "name9",
    0x6E325104: "name10",
    0x2AB3C64D: "name11",
    0x124F817B: "name12",
    0x053A933E: "name13",
    0x92DA2570: "name14",
    0x6664D204: "name15",
    0x07AD83B4: "name16",
    0x50A87B27: "near_val",

    0xE82E1EE9: "objID",
    0xC1C46A42: "objModel",
    0x3AAEA627: "objName",
    0x8ED2FA8C: "objType",
    0x5B0CDAF3: "obj_name",
    0xBE50E8FF: "opFadeColB",
    0xDF895D4D: "opFadeColG",
    0x7BC6D53E: "opFadeColR",
    0x2C03405F: "opFadeIn",
    0x58D8E982: "opFadeInEnable",
    0x1E475B80: "opFadeOut",
    0xC513418E: "opFadeOutEnable",
    0x4F74D178: "opFadeWait",
    0xB3254010: "option_id",
    0xD3309DD9: "outsiderEnable",
    0xFFCB5A95: "outsiderOpt",
    0x216638BA: "outsiderR",
    0xAC1E80E2: "outsiderType",
    0x7966F2EA: "outsiderX",
    0x038BF950: "outsiderY",
    0x97CECB49: "outsiderZ",

    0x3CE8BB61: "pad_A",
    0xD4AE2271: "pad_B",
    0x4A578692: "pad_DOWN",
    0xF31ABAB8: "pad_L1",
    0x2FD4671B: "pad_L2",
    0xFFE3CE06: "pad_L3",
    0x28DE6F1B: "pad_LEFT",
    0xC9C9AA66: "pad_LS_DOWN",
    0x87227ECF: "pad_LS_LEFT",
    0x92458260: "pad_LS_RIGHT",
    0xE7E748AC: "pad_LS_UP",
    0x2B47CBF8: "pad_R1",
    0x54407E02: "pad_R2",
    0x340CED85: "pad_R3",
    0x088C2436: "pad_RIGHT",
    0x8A1D575F: "pad_RS_DOWN",
    0x0E9DAE7E: "pad_RS_LEFT",
    0xD058E6DB: "pad_RS_RIGHT",
    0xDB3F3E82: "pad_RS_UP",
    0x2DFA1572: "pad_SELECT",
    0xA82F8150: "pad_START",
    0xD53E58DA: "pad_UP",
    0x6A135274: "pad_X",
    0x531B6467: "pad_Y",
    0x3519EFE3: "pad_select",
    0x811DBDD3: "partition",
    0x1B25F9CD: "path_prefix",
    0xE101AC67: "pc",
    0x03A8508C: "physical",
    0xF4080FD7: "picid",
    0x4F8DF293: "pitchHigh",
    0x1D7AA6DC: "pitchLow",
    0xCFD2E556: "pixel",
    0xBA7E3F4D: "pixelLv",
    0x5EE13107: "playMap",
    0xC36A60C3: "pos1",
    0xFCB4D119: "pos2",
    0xAA7A4036: "pos3",
    0x45628554: "pos4",
    0x9AAFDC76: "pos5",
    0x54377070: "pos6",
    0xE4A9F8AB: "pos7",
    0xD3D9068F: "pos8",
    0x99F75999: "pos9",
    0x0832D6A6: "pos10",
    0xEA395117: "pos11",
    0x422DBE87: "pos12",
    0x24AD9D8D: "pos13",
    0xD882DE41: "pos14",
    0xD2048758: "pos15",
    0x83EA6C30: "pos16",
    0x7042084E: "posX",
    0x459752D9: "posY",
    0x89D9F91C: "posZ",
    0x3D17AA93: "posx",
    0x0ECD83BF: "posy",
    0x29C32CDA: "posz",
    0xEA70AF69: "prio",
    0xAEFAEA7E: "push_type",  # FIXME: unclear if correct

    0x3F28C38D: "quads",

    0x17EAB7D3: "race",
    0x4C77A395: "range",
    0x5518760A: "rank",
    0x9A50D505: "rate1",
    0x7DDF48DE: "rate2",
    0x6A5BC8E6: "rate3",
    0x0FF75091: "rate4",
    0x52CDC330: "rate5",
    0xE3F05B02: "rate6",
    0x32A2EF10: "rate7",
    0x54BB9C30: "rate8",
    0x8AEB5595: "rate9",
    0x244734BF: "rate10",
    0x26374320: "repeat",
    0x1D9F0854: "res_type",
    0x40307D1F: "resource",
    0x3F0EA114: "resourceAnnotation",
    0xD5F5DF3D: "resourceBody",
    0xB3A45D50: "resourceFace",
    0xA101EADB: "resourceHair",
    0x268DC11D: "roty",

    0x224F4F87: "save",
    0xE420AC79: "scaleX",
    0x71D673E6: "scaleY",
    0x2A70A483: "scale_max",
    0x0CE3A32A: "scale_min",
    0xC9C8A329: "scenario",
    0x19790F4C: "scn_category",
    0xB14ADE30: "scn_group",
    0x3FB155BA: "select_text",
    0x4052B8AE: "setupID",
    0xCD0160E7: "setupName",
    0x55819099: "sex",
    0x5D9E2609: "shift",
    0xADE813C5: "sort_id",
    0x85942DBE: "sort_index",
    0x50694846: "spWeapon",
    0x995AD550: "specified",
    0x3B74D6A2: "speed",
    0xFD4EDE72: "startID",
    0x0AAFDDB0: "strength",
    0x554EE944: "style",

    0xC624AE24: "text",
    0x7E730326: "text2",
    0x6477F5E6: "text3",
    0x2CC354E5: "text4",
    0x363C44F1: "text_file",
    0x1A88A3DE: "text_id",
    0x2ABA9045: "text_type",
    0x73059C21: "timeHour",
    0xBABF6EC2: "timeMinute",
    0xCBF6AE21: "tips",
    0xE4ED1C77: "title",
    0x58C4B2E6: "toneMap",
    0xD62E5B05: "top_id",
    0x79F23513: "type",
    0xC08A263F: "type1",
    0x2FB8DE0B: "type2",
    0xA40D9623: "type3",
    0xFFC86099: "type4",
    0x0B7F31E3: "type5",
    0xCF331112: "type6",
    0x3870AC04: "type7",
    0xD2D81FB4: "type8",
    0x002497C8: "type9",
    0x459FCDF6: "type10",
    0x34A6133C: "type11",
    0x3B81B654: "type12",
    0x263483D3: "type13",
    0x53AC2A06: "type14",
    0x532A5E1D: "type15",
    0x10B3628E: "type16",

    0x3E472BA3: "unique",

    0xD9093F6E: "value",
    0xD7F1DC75: "value1",
    0xBF6CEA56: "value2",
    0xF5A78C0D: "value3",
    0x01D49138: "value4",
    0x06E04522: "value5",
    0x02CEE7E2: "value6",
    0x19111361: "value7",
    0xDF15DB52: "value8",
    0xF5D567D3: "value9",
    0x6D84B3E7: "value10",
    0x4C6F31C3: "view_type",
    0xC8B28F74: "voice",
    0x53DD6A09: "vol_id",

    0xEA4F656D: "waitComp",
    0x47F7A3DE: "weather1",
    0x15AC9BA0: "weather2",
    0xF7FD283B: "weatherA",
    0x36631CE0: "weatherB",
    0x2304374E: "weatherC",
    0xD8947E5A: "window_disp",
    0xCC9965C3: "wpnBlade",

    0x9ACE1789: "x1",
    0x31CECC20: "x2",
    0xCFF8B760: "x3",
    0xFDC17DCC: "x4",
    0xE38DBDCE: "x5",
    0x0577A76C: "x6",
    0x7C01D948: "x7",
    0x3825B0F1: "x8",
    0x5F600E3B: "x9",
    0x64B34622: "x10",
    0x563F52C2: "x11",
    0xE3208515: "x12",
    0xEF78D9D5: "x13",
    0x8EB54B3E: "x14",
    0x03D342DA: "x15",
    0x03083977: "x16",

    0x459CCD21: "y1",
    0x465D05FA: "y2",
    0x3FAD0B3C: "y3",
    0x69972DCC: "y4",
    0xE3A1147A: "y5",
    0xD4725C31: "y6",
    0x786ED396: "y7",
    0x7CE7C522: "y8",
    0x282C6611: "y9",
    0xF371BE5A: "y10",
    0xE507D474: "y11",
    0x09B5FC4C: "y12",
    0x5B4FAC34: "y13",
    0x52A92AED: "y14",
    0x4DEDF58D: "y15",
    0x2A43CC7A: "y16",

    0x46F84638: "z1",
    0xD45CC048: "z2",
    0x660A6AB0: "z3",
    0x3CD5F972: "z4",
    0x068C9A39: "z5",
    0x9598B98D: "z6",
    0xA39B6A27: "z7",
    0x2B5B1FB5: "z8",
    0x78B10BF1: "z9",
    0x99767281: "z10",
    0x24B37ADA: "z11",
    0x0371032F: "z12",
    0x615C8F68: "z13",
    0xC32C8198: "z14",
    0x39B9FFDA: "z15",
    0x8B8A1BF1: "z16",
}

def unhash(hash, default=None):
    """Return the string corresponding to a hash, or the default if unknown."""
    value = hashes.get(hash, default)
    return value if value is not None else default


########################################################################
# Basic script data constants/structures

class BdatValueType(enum.Enum):
    """Enumeration of value types."""
    BOOL = 0  # Not in actual data; used internally for flag fields.
    UINT8 = 1
    UINT16 = 2
    UINT32 = 3
    SINT8 = 4
    SINT16 = 5
    SINT32 = 6
    STRING = 7
    FLOAT32 = 8
    HSTRING = 9  # 32-bit Murmur3 hashed string (introduced in XC3)
    PERCENT = 10  # Signed byte * 0.01 (introduced in XC3)
    UNK_11 = 11  # FIXME: unknown 4-byte type (introduced in XC3)
    UNK_12 = 12  # FIXME: unknown 1-byte type (introduced in XC3)
    UNK_13 = 13  # FIXME: unknown 2-byte type (introduced in XC3)


class BdatFieldType(enum.Enum):
    """Enumeration of field types."""
    SCALAR = 1
    ARRAY = 2
    FLAG = 3  # Rewritten to SCALAR/BOOL internally.


class BdatField(object):
    """Class describing a single field of a BDAT table."""

    def __init__(self, name, field_type, value_type, array_size=None):
        assert isinstance(name, str)
        assert isinstance(field_type, BdatFieldType)
        assert isinstance(value_type, BdatValueType)
        self._name = name
        self._field_type = field_type
        self._value_type = value_type
        self._array_size = array_size

    @property
    def name(self):
        """The name of this field."""
        return self._name

    @property
    def field_type(self):
        """The field type (scalar, array, flag) of this field."""
        return self._field_type

    @property
    def value_type(self):
        """The value type (int, string, ...) of this field."""
        return self._value_type

    @property
    def array_size(self):
        """The length of this array field.  None if not an array field."""
        return self._array_size


_global_hashmap = {}


class BdatTable(object):
    """Class wrapping a single table from a BDAT file."""

    _global_hashmap = {}

    @staticmethod
    def global_id_lookup(id):
        """Return the table and row index corresponding to the given ID."""
        return _global_hashmap.get(id, (None, None))

    def __init__(self, name, fields, rows):
        """Initialize a BdatTable instance.

        Parameters:
            name: Table name.
            fields: List of table fields (BdatField instances).
            rows: List of data rows.  Each row must be a list containing
                one value for each element of "fields".
        """
        assert isinstance(name, str)
        assert len(name) > 0
        for row in rows:
            assert len(row) == len(fields)
            for i in range(len(fields)):
                if fields[i].array_size is not None:
                    assert islistlike(row[i])
                    assert len(row[i]) == fields[i].array_size
        self._name = name
        self._fields = fields
        self._rows = rows
        self._refs = [None] * len(rows)
        self._hashid_map = {}
        try:
            if self._fields[1].name in ('ID', 'label') and self._fields[1].value_type == BdatValueType.HSTRING:
                for row in range(len(self._rows)):
                    id = self._rows[row][1]
                    self._hashid_map[id] = row
                    if id in _global_hashmap:
                        # Don't bother warning about these because
                        # murmur3 generates Very Many of them
                        #print(f'Global ID collision: {id}', file=sys.stderr)
                        _global_hashmap[id] = (None, None)
                    else:
                        _global_hashmap[id] = (self._name, row)
        except ValueError:
            pass

    @property
    def name(self):
        """The name of this table."""
        return self._name

    @property
    def num_fields(self):
        """The number of fields in this table."""
        return len(self._fields)

    @property
    def num_rows(self):
        """The number of rows in this table."""
        return len(self._rows)

    def field(self, index):
        """Return the given field in this table."""
        assert index >= 0 and index < len(self._fields)
        return self._fields[index]

    def field_index(self, name):
        """Return the index of the given field in this table.  The first
        field (index 0) is not considered.

        If the table has multiple fields with the same index, the first one
        is returned.
        """
        for i in range(1, len(self._fields)):
            if self._fields[i].name == name:
                return i
        raise ValueError(f'Field {name} not found in table {self._name}')

    def id_to_row(self, id):
        """Return the row index corresponding to the given numeric or hash ID.

        If id is an int, the row index returned is id - base_id (the base ID
        encoded in the table).  Otherwise id must be a string of the form
        <HASH_VAL> (HASH_VAL being 8 uppercase hexadecimal digits), and the
        row index returned is the row whose hash-type ID value is the given
        hash value.

        If id is out of range (when numeric) or not found (when a hash),
        None is returned.
        """
        if isinstance(id, int):
            row_index = id - self._rows[0][0]
            if row_index >= 0 and row_index < len(self._rows):
                return row_index
            return None
        else:
            assert isinstance(id, str)
            return self._hashid_map.get(id, None)

    def get(self, row, field):
        """Return the content of the given cell."""
        assert row < len(self._rows)
        assert field < len(self._fields)
        if isinstance(self._rows[row][field], tuple):
            return self._rows[row][field][0]
        else:
            return self._rows[row][field]

    def set(self, row, field, value, link_table=None, link_row=None):
        """Set the content of the given cell to the given value and optional
        table link.

        [Parameters]
            row: Row index.
            field: Field index.
            value: Value to set.
            link_table: Name of table to which to link.
            link_row: ID of row to which to link.
        """
        assert row < len(self._rows)
        assert field < len(self._fields)
        assert value is not None
        if link_table:
            assert isinstance(link_table, str)
            assert link_row is not None
            self._rows[row][field] = (value, link_table, link_row)
        else:
            self._rows[row][field] = value

    def addref(self, row, ref_name, ref_row, ref_value):
        """Add a reference to the given row from the named table and row.
        
        [Parameters]
            row: Row in this table which is referenced.
            ref_name: Name of the referencing table.
            ref_row: ID of the referencing row in the referencing table.
        """
        assert row < len(self._rows)
        assert isinstance(ref_name, str)
        if not self._refs[row]:
            self._refs[row] = set()
        self._refs[row].add((ref_name, ref_row, ref_value))

    # Styling/scripting adapted from https://github.com/Thealexbarney/XbTool
    _HTML_HEADER = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta http-equiv="Content-Style-Type" content="text/css" />
  <title>{title}</title>
  <style type="text/css">
    table, th, td {border: 1px solid #000000; border-collapse: collapse;}
    table {border-width: 3px;}
    th, td {padding: 0.1em 0.2em;}
    tr.head th, tr.head td {border-bottom-width: 3px;}
    th.colbreak, td.colbreak {border-right-width: 3px;}
    th {text-align: center; position: sticky; top: -1px; background-color: #F0F0F0;}
    .side {position: sticky; left: -1px; background-color: #F0F0F0;}
    th.side {z-index: 3;}
    td {text-align: left;}
    td.right {text-align: right;}
    .sortable tbody tr:nth-child(odd) {background: #F5F5F5;}
    .sortable th {background: #E4E4E4; cursor: pointer; white-space: nowrap; vertical-align: middle;}
    .sortable th.dir-d::after {content:" ▾"; vertical-align: inherit;}
    .sortable th.dir-u::after {content:" ▴"; vertical-align: inherit;}
    :target td {background-color: #CCCCCC !important;}
  </style>
  <script type="text/javascript">
    function offsetAnchor() {
      if (location.hash.length !== 0) {
        window.scrollTo(window.scrollX, window.scrollY - document.getElementById("header").clientHeight);
      }
    }
    window.addEventListener("hashchange", offsetAnchor);
    window.setTimeout(offsetAnchor, 1);
  </script>
</head>
<body>
  <table class="sortable">
    <h2>{title}</h2>
"""

    _HTML_FOOTER = """  </table>
</body>
</html>
"""

    def print(self):
        """Return a string containing this table in HTML format."""
        s = self._HTML_HEADER.replace('{title}', self.name)
        s += '    <tr id="header">\n'
        s += '      <th class="side dir-d ">ID</th>\n'
        s += '      <th>Referenced By</th>\n'
        for f in self._fields[1:]:
            colspan = '' if f.array_size is None else f' colspan="{f.array_size}"'
            s += f'      <th{colspan}>{f.name}</th>\n'
        s += '    </tr>\n'
        for i in range(len(self._rows)):
            row = self._rows[i]
            id = row[0]
            s += f'    <tr id="{id}">\n'
            s += f'      <td class="side">{id}</td>\n'
            if self._refs[i]:
                s += f'      <td>\n'
                s += f'        <details>\n'
                s += f'          <summary>{len(self._refs[i])} refs</summary>\n'
                for ref in sorted(self._refs[i], key=lambda x: f'x[0]#x[1]'):
                    s += f'          <a href="{ref[0]}.html#{ref[1]}">{ref[0]}#{ref[2]}</a>\n'
                s += f'        </details>\n'
                s += f'      </td>\n'
            else:
                s += f'      <td></td>\n'
            for i in range(1, len(self._fields)):
                if self._fields[i].array_size is None:
                    values = (row[i],)
                else:
                    values = row[i]
                for value in values:
                    if isinstance(value, tuple):
                        value_str = (f'<a href="{value[1]}.html#{value[2]}">'
                                     + self._print_value(value[0], self._fields[i])
                                     + '</a>')
                    else:
                        value_str = self._print_value(value, self._fields[i])
                    s += f'      <td>{value_str}</td>\n'
            # end for
            s += '    </tr>\n'
        s += self._HTML_FOOTER
        return s

    def _print_value(self, value, field):
        """Return the given value formatted for HTML."""
        if value is None:
            s = ''
        elif field.value_type == BdatValueType.FLOAT32:
            s = f'{value:.6g}'
        else:
            s = str(value)
        return self._quote(s)

    @staticmethod
    def _quote(s):
        """Return the given string quoted according to HTML rules."""
        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('\n', '<br />')
        return s


class Bdat(object):
    """Class wrapping a BDAT file."""

    def __init__(self, path):
        """Initialize a Bdat isntance.

        Parameters:
            path: Pathname of the BDAT file.

        Raises:
            OSError: Raised if the file cannot be read.
        """
        self.path = path  # For external reference.
        self.name = os.path.basename(path)  # For external reference.
        with open(path, 'rb') as f:
            self._tables = self._parse(f.read())

    def tables(self):
        """Return a list of tables contained in this BDAT file."""
        return list(self._tables)  # Make a copy.

    def _parse(self, data):
        """Parse the given data as a BDAT file.

        Parameters:
            data: BDAT file data, as a bytes.

        Return value:
            List containing one BdatTable instance for each table in the file.

        Raises:
            ValueError: Raised on a data format error.
        """
        if len(data) < 4:
            raise ValueError('File is too short')
        if data[0:4] == b'BDAT':
            if len(data) < 12:
                raise ValueError('File is too short')
            if u32(data, 4) != 0x01001004:
                raise ValueError('Unexpected word 0x4')
            self._version = 2
            offset = 8
        else:
            self._version = 1
            offset = 0
        num_tables = u32(data, offset)
        if num_tables <= 0:
            raise ValueError(f'Invalid table count {num_tables}')
        if len(data) < offset + 8 + 4*num_tables:
            raise ValueError('File is too short')
        return list(self._parseTable(data, u32(data, offset+8+4*i))
                    for i in range(num_tables))

    def _parseTable(self, data, offset):
        """Parse a single table from a BDAT file.

        Parameters:
            data: BDAT file data, as a bytes.
            offset: Byte offset of the beginning of the table.

        Return value:
            BdatTable instance for the table.

        Raises:
            ValueError: Raised on a data format error.
        """
        if self._version == 2:
            return self._parseTable2(data, offset);
        else:
            return self._parseTable1(data, offset);

    def _parseTable1(self, data, offset):
        """Parse a single table from a version 1 (XCX/XC2/XCDE) BDAT file."""
        if len(data) < offset+36:
            raise ValueError(f'Table at 0x{offset:X}: Truncated data or invalid offset')
        if data[offset:offset+4] != b'BDAT':
            raise ValueError(f'Table at 0x{offset:X}: Invalid header')
        (encryption, names_ofs, row_size, hash_ofs, hash_size, rows_ofs,
         row_count, base_id, _, checksum, strings_ofs, strings_size,
         fields_ofs, field_count) = struct.unpack('<HHHHHHHHHHIIHH',
                                                   data[offset+4:offset+36])
        end_ofs = offset + max(hash_ofs + hash_size,
                               rows_ofs + row_size * row_count,
                               strings_ofs + strings_size,
                               fields_ofs + 6 * field_count)
        if len(data) < end_ofs:
            raise ValueError(f'Table at 0x{offset:X}: Truncated data')
        tdata = bytearray(data[offset:end_ofs])

        if encryption == 2:
            self._decrypt(tdata, names_ofs, hash_ofs - names_ofs, checksum)
            self._decrypt(tdata, strings_ofs, strings_size, checksum)
        elif encryption != 0:
            raise ValueError(f'Table at 0x{offset:X}: Invalid encryption flag {encryption}')

        table_name = self._stringz(tdata, names_ofs, hash_ofs)

        fields = [(BdatField('ID', BdatFieldType.SCALAR, BdatValueType.UINT32), None, None)]
        for i in range(field_count):
            info_ofs = u16(tdata, fields_ofs+i*6)
            name = self._stringz(tdata, u16(tdata, fields_ofs+i*6+4))
            field_type = BdatFieldType(tdata[info_ofs+0])
            if field_type == BdatFieldType.FLAG:
                field_type = BdatFieldType.SCALAR
                value_type = BdatValueType.BOOL
                flag_index, flag_mask, parent_ofs = struct.unpack(
                    '<BIH', tdata[info_ofs+1:info_ofs+8])
                parent_info_ofs = u16(tdata, parent_ofs)
                if tdata[parent_info_ofs+0] != BdatFieldType.SCALAR.value:
                    raise ValueError(f"Table {table_name} field {name}: flag field's parent value is not a scalar")
                if tdata[parent_info_ofs+1] == BdatValueType.UINT8.value:
                    flag_size = 1
                elif tdata[parent_info_ofs+1] == BdatValueType.UINT16.value:
                    flag_size = 2
                elif tdata[parent_info_ofs+1] == BdatValueType.UINT32.value:
                    flag_size = 4
                else:
                    raise ValueError(f"Table {table_name} field {name}: flag field's parent value is not an unsigned integer")
                flag_ofs = u16(tdata, parent_info_ofs+2)
                array_size = None
            else:
                value_type = BdatValueType(tdata[info_ofs+1])
                value_ofs = u16(tdata, info_ofs+2)
                flag_ofs = None
                flag_size = None
                flag_mask = None
                if field_type == BdatFieldType.ARRAY:
                    array_size = u16(tdata, info_ofs+4)
                else:
                    array_size = None
            fields.append((BdatField(name, field_type, value_type, array_size), value_ofs, flag_ofs, flag_size, flag_mask))
        # end for

        rows = []
        for i in range(row_count):
            row = [base_id + i]
            for field, value_ofs, flag_ofs, flag_size, flag_mask in fields[1:]:
                if flag_ofs is not None:
                    size = flag_size
                    if size == 1:
                        unpack = 'B'
                    elif size == 2:
                        unpack = 'H'
                    elif size == 4:
                        unpack = 'I'
                    else:
                        assert False
                elif field.value_type == BdatValueType.UINT8:
                    unpack = 'B'
                    size = 1
                elif field.value_type == BdatValueType.UINT16:
                    unpack = 'H'
                    size = 2
                elif field.value_type == BdatValueType.UINT32:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.SINT8:
                    unpack = 'b'
                    size = 1
                elif field.value_type == BdatValueType.SINT16:
                    unpack = 'h'
                    size = 2
                elif field.value_type == BdatValueType.SINT32:
                    unpack = 'i'
                    size = 4
                elif field.value_type == BdatValueType.STRING:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.FLOAT32:
                    unpack = 'f'
                    size = 4
                else:
                    assert False
                if field.array_size is not None:
                    size *= field.array_size
                    unpack = str(field.array_size) + unpack
                value_ofs += rows_ofs + i * row_size
                values = struct.unpack('<'+unpack, tdata[value_ofs:value_ofs+size])
                if field.value_type == BdatValueType.STRING:
                    values = list(self._stringz(tdata, ofs) for ofs in values)
                if flag_ofs is not None:
                    value = ((values[0] & flag_mask) != 0)
                elif field.array_size is not None:
                    value = values
                else:
                    value = values[0]
                row.append(value)
            # end for
            rows.append(row)
        # end for

        return BdatTable(table_name, list(f[0] for f in fields), rows)

    def _parseTable2(self, data, offset):
        """Parse a single table from a version 2 (XC3) BDAT file."""
        if len(data) < offset+48:
            raise ValueError(f'Table at 0x{offset:X}: Truncated data or invalid offset')
        if data[offset:offset+4] != b'BDAT' or u32(data, offset+4) != 0x3004:
            raise ValueError(f'Table at 0x{offset:X}: Invalid header')
        # Value at 0x14: unknown, looks like a string hash and is zero in single-table files like msg_*
        # Note that the hash at offset 0x5 in the string table seems to be zero iff the value here at 0x14 is zero
        (field_count, row_count, base_id, _, fields_ofs, hash_ofs, rows_ofs,
         row_size, strings_ofs, strings_size) = \
                struct.unpack('<IIIIIIIIII', data[offset+8:offset+48])
        end_ofs = offset + max(fields_ofs + 3 * field_count,
                               hash_ofs + 8 * row_count,
                               rows_ofs + row_size * row_count,
                               strings_ofs + strings_size)
        if len(data) < end_ofs:
            raise ValueError(f'Table at 0x{offset:X}: Truncated data')
        tdata = bytearray(data[offset:end_ofs])

        table_name = u32(tdata, strings_ofs+1)
        if table_name != 0:
            table_name = unhash(table_name, f'{table_name:08X}')
        else:
            table_name = self.name.replace('.bdat', '')

        raw_field_names = tdata[strings_ofs]
        fields = [BdatField('ID', BdatFieldType.SCALAR, BdatValueType.UINT32)]
        for i in range(field_count):
            type = BdatValueType(tdata[fields_ofs+i*3+0])
            name_ofs = u16(tdata, fields_ofs+i*3+1)
            if raw_field_names:
                name = self._stringz(tdata, strings_ofs + name_ofs)
            else:
                name = u32(tdata, strings_ofs + name_ofs)
                name = unhash(name, f'field_{name:08X}')
            fields.append(BdatField(name, BdatFieldType.SCALAR, type))

        rows = []
        for i in range(row_count):
            row = [base_id + i]
            value_ofs = rows_ofs + i * row_size
            for field in fields[1:]:
                if field.value_type == BdatValueType.UINT8:
                    unpack = 'B'
                    size = 1
                elif field.value_type == BdatValueType.UINT16:
                    unpack = 'H'
                    size = 2
                elif field.value_type == BdatValueType.UINT32:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.SINT8:
                    unpack = 'b'
                    size = 1
                elif field.value_type == BdatValueType.SINT16:
                    unpack = 'h'
                    size = 2
                elif field.value_type == BdatValueType.SINT32:
                    unpack = 'i'
                    size = 4
                elif field.value_type == BdatValueType.STRING:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.FLOAT32:
                    unpack = 'f'
                    size = 4
                elif field.value_type == BdatValueType.HSTRING:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.PERCENT:
                    unpack = 'b'
                    size = 1
                elif field.value_type == BdatValueType.UNK_11:
                    unpack = 'I'
                    size = 4
                elif field.value_type == BdatValueType.UNK_12:
                    unpack = 'B'
                    size = 1
                elif field.value_type == BdatValueType.UNK_13:
                    unpack = 'H'
                    size = 2
                else:
                    assert False
                value = struct.unpack('<'+unpack, tdata[value_ofs:value_ofs+size])[0]
                value_ofs += size
                if field.value_type == BdatValueType.STRING:
                    value = self._stringz(tdata, strings_ofs + value)
                elif field.value_type == BdatValueType.HSTRING:
                    value = unhash(value, f'<{value:08X}>')
                elif field.value_type == BdatValueType.PERCENT:
                    value *= 0.01
                row.append(value)
            # end for
            rows.append(row)
        # end for

        return BdatTable(table_name, fields, rows)

    def _stringz(self, data, offset, limit = 0):
        """Return a null-terminated UTF-8 string from a data buffer."""
        if limit == 0:
            limit = len(data)
        end = offset
        while end < limit:
            if data[end] == 0:
                return data[offset:end].decode('utf-8')
            end += 1
        raise ValueError(f'Null-terminated string at 0x{offset:X} overruns next data element')

    def _hash(self, s, hash_size = 0):
        """Return the hash value of the given string."""
        value = 0
        for i in range(min(len(s), 8)):
            assert s[i] < 0x80
            value = 7*value + s[i]
        return value % hash_size if hash_size else value

    def _decrypt(self, data, offset, size, key):
        """Decrypt (in place) a section of a BDAT table."""
        if size % 2 != 0:
            raise ValueError(f'Odd size for encrypted section at 0x{offset:X}+0x{size:X}')
        a = (~key >> 8) & 255
        b = ~key & 255
        for i in range(0, size, 2):
            x = data[offset+i+0]
            y = data[offset+i+1]
            data[offset+i+0] ^= a
            data[offset+i+1] ^= b
            a = (a + x) & 255
            b = (b + y) & 255


########################################################################
# Table cross-reference resolution
# (note: these apply only to XC3 tables)

# List of table row-name fields.
# If a table has a row-name field, then reference links to that table will
# use the row's value for that field (if not empty) in place of the row ID.
row_name_fields = {
    'BTL_Achievement': 'Caption',
    'BTL_Arts_En': 'Name',
    'BTL_Arts_PC': 'Name',
    'BTL_Combo': 'Name',
    'BTL_Enhance': 'Caption',
    'BTL_MotionState': 'StateName',
    'BTL_Reaction': 'Name',
    'BTL_Skill_PC': 'Name',
    'BTL_Talent': 'Name',
    'CHR_PC': 'Name',
    'CHR_UroBody': 'Name',
    'FLD_ColonyList': 'Name',
    'FLD_CookRecipe': 'Name',
    'FLD_NpcList': 'field_7F0A3296',
    'FLD_NpcResource': 'Name',
    'FLD_NpcResource': 'Name',
    'ITM_Accessory': 'Name',
    'ITM_Collection': 'Name',
    'ITM_Collepedia': 'Text',
    'ITM_Cylinder': 'Name',
    'ITM_Gem': 'Name',
    'ITM_Info': 'Name',
    'ITM_Precious': 'Name',
    'MNU_MapInfo': 'disp_name',
    'MNU_ShopList': 'Name',
    'QST_List': 'QuestTitle',
    'QST_RequestItemSet': 'Name',
    'QST_Task': 'TaskLog1',
    'SYS_TutorialMessage': 'Title',
    'SYS_TutorialSummary': 'Title',
    'SYS_TutorialTask': 'Title',
    '03B52788': 'Title',
    '2521C473': 'MsgName',
    '6EC8096C': 'Name',
    'BB82DEE6': 'Name',
    'D9B88F26': 'Name',
}

# List of direct references from tables to text strings.
# Value format: {'source_field_name': ('target_table', 'target_field_name' [, 'special_rule'])}
# A source (ID) value of zero is converted to an empty cell.
text_xrefs = {
    'BTL_Achievement': {'Caption': ('825EDC88', 'name', 'achievement')},
    'BTL_Arts_En': {'Name': ('msg_btl_arts_en_name', 'name')},
    'BTL_Arts_PC': {'Name': ('msg_btl_arts_name', 'name'),
                    'Caption': ('7E210829', 'name')},
    'BTL_Combo': {'Name': ('A391C96F', 'name')},
    'BTL_Enhance': {'Caption': ('msg_btl_enhance_cap', 'name', 'enhance')},
    'BTL_Reaction': {'Name': ('A391C96F', 'name')},
    'BTL_Skill_PC': {'Name': ('DC74E779', 'name')},
    'BTL_Talent': {'Name': ('EA640EBA', 'name')},
    'CHR_PC': {'Name': ('BA34C46E', 'name')},
    'CHR_UroBody': {'Name': ('32E2F16E', 'name', 'urobody_name')},
    'FLD_ColonyList': {'Name': ('C617D216', 'name'),
                       'Caption': ('9B911635', 'name')},
    'FLD_CookRecipe': {'Name': ('8B7D949B', 'name')},
    'FLD_NpcList': {'field_7F0A3296': ('FLD_NpcResource', 'Name')},
    'FLD_NpcResource': {'Name': ('6436BD4A', 'name'),
                        'Nickname': ('EDFB4E9F', 'name')},
    'ITM_Accessory': {'Name': ('9AA4C028', 'name')},
    'ITM_Collection': {'Name': ('133CD173', 'name')},
    'ITM_Collepedia': {'Text': ('BEDB6533', 'name'),
                       'Text2': ('BEDB6533', 'name')},
    'ITM_Cylinder': {'Name': ('24810A75', 'name')},
    'ITM_Gem': {'Name': ('D0A5476B', 'name')},
    'ITM_Info': {'Name': ('CA2198EC', 'name')},
    'ITM_Precious': {'Name': ('3550B295', 'name'),
                     'Caption': ('3550B295', 'name'),
                     'Name2': ('3550B295', 'name'),
                     'Caption2': ('3550B295', 'name')},
    'MNU_MapInfo': {'disp_name': ('5DFDA895', 'name')},
    'MNU_ShopList': {'Name': ('16B245E3', 'name')},
    'QST_List': {'QuestTitle': ('msg_qst_task', 'name'),
                 'Summary': ('msg_qst_task', 'name'),
                 'ResultA': ('msg_qst_task', 'name'),
                 'ResultB': ('msg_qst_task', 'name')},
    'QST_RequestItemSet': {'Name': ('msg_qst_RequestItemSet', 'name')},
    'QST_Task': {'TaskLog1': ('msg_qst_task', 'name'),
                 'TaskLog2': ('msg_qst_task', 'name')},
    'SYS_TutorialHintA': {'Text1': ('BBF540E7', 'name'),
                          'Text2': ('BBF540E7', 'name')},
    'SYS_TutorialMessage': {'Title': ('BBF540E7', 'name'),
                            'Text': ('BBF540E7', 'name'),
                            'Text2': ('BBF540E7', 'name')},
    'SYS_TutorialSummary': {'Title': ('BBF540E7', 'name')},
    'SYS_TutorialTask': {'Title': ('BBF540E7', 'name')},
    '03B52788': {'Title': ('BBF540E7', 'name')},  # Tutorial battle list
    '2521C473': {'MsgName': ('122A06D4', 'name')},  # Enemy list
    '6EC8096C': {'Name': ('0103F5B8', 'name')},  # Canteen recipe list
    'BB82DEE6': {'Name': ('F6E689C3', 'name')},  # Chain attack TP bonuses
    'D9B88F26': {'Name': ('FC27D14D', 'name')},  # Chain attack card list
    'EED24855': {'GroupName': ('4CF32197', 'name')},  # Unique monster list
    # Per-map(?) enemy lists
    'gimmickEnemyPop': {'GroupName': ('4CF32197', 'name')},
    '0277EA4F': {'GroupName': ('4CF32197', 'name')},
    '0CD3B481': {'GroupName': ('4CF32197', 'name')},
    '232003CA': {'GroupName': ('4CF32197', 'name')},
    '6999DAFE': {'GroupName': ('4CF32197', 'name')},
    '778E3103': {'GroupName': ('4CF32197', 'name')},
    '7A517BD1': {'GroupName': ('4CF32197', 'name')},
    '7BECF394': {'GroupName': ('4CF32197', 'name')},
    'B7FACD23': {'GroupName': ('4CF32197', 'name')},
    'C76401A3': {'GroupName': ('4CF32197', 'name')},
    'F4C65A41': {'GroupName': ('4CF32197', 'name')},
}
# 9760BC94: hero names with titles (Silvercoat Ethel etc)

refset_arts_en = ('BTL_Arts_En', )
refset_arts_pc = ('BTL_Arts_PC', )
refset_condition = ('FLD_ConditionList', )
refset_enemy = ('2521C473', )
refset_enhance = ('BTL_Enhance', )
refset_event = (('23EE284B', '25B62687', 'BB0F57A4', '5B1D40C4'), )
refset_item = (('ITM_Accessory', 'ITM_Collection', 'ITM_Collepedia', 'ITM_Cylinder', 'ITM_Gem', 'ITM_Info', 'ITM_Precious'), )
refset_npc = ('FLD_NpcList', )
refset_pc = ('CHR_PC', )
refset_quest = ('QST_List', )
refset_quest_taskid = (('QST_TaskAsk', 'QST_TaskBattle', 'QST_TaskChase', 'QST_TaskCollect', 'QST_TaskCollepedia', 'QST_TaskCondition', 'QST_TaskEvent', 'QST_TaskFollow', 'QST_TaskGimmick', 'QST_TaskReach', 'QST_TaskRequest', 'QST_TaskTalk', 'QST_TaskTalkGroup'), )
refset_skill = ('BTL_Skill_PC', )
refset_talent = ('BTL_Talent', )

# List of fields which are always ID references to other tables.
# Each value is in one of the following formats, with the ID value
# replaced by text as listed:
#    - 'target_table'
#         No text substitution performed on ID.
#    - ('target_table', 'name_field')
#         ID replaced by text from field 'name_field' in the target row.
#         If that field is empty, the ID is left unchanged.
#    - ('target_table', 'name_field', 'special_rule')
#         ID replaced by text from field 'name_field' in the target row,
#         and subsequently modified according to 'special_rule' (see code
#         in resolve_field_xrefs()).
# A zero ID is always converted to an empty cell.
field_xrefs = {
    'Colony': 'FLD_ColonyList',
    'ColonyID': 'FLD_ColonyList',
    'ColonyID1': 'FLD_ColonyList',
    'ColonyID2': 'FLD_ColonyList',
    'ColonyID3': 'FLD_ColonyList',

    'Condition': refset_condition,
    'Condition1': refset_condition,
    'Condition2': refset_condition,
    'Condition3': refset_condition,
    'Condition4': refset_condition,
    'Condition5': refset_condition,
    'Condition6': refset_condition,

    'CookRecipe': 'FLD_CookRecipe',

    'EnemyID': refset_enemy,
    'EnemyID1': refset_enemy,
    'EnemyID2': refset_enemy,
    'EnemyID3': refset_enemy,
    'EnemyID4': refset_enemy,
    'EnemyID5': refset_enemy,
    'EnemyID6': refset_enemy,
    'EnemyID01': refset_enemy,
    'EnemyID02': refset_enemy,
    'EnemyID03': refset_enemy,

    'Enhance': refset_enhance,
    'Enhance1': refset_enhance,
    'Enhance2': refset_enhance,
    'Enhance3': refset_enhance,
    'Enhance4': refset_enhance,
    'Enhance5': refset_enhance,
    'EnhanceID': refset_enhance,

    'EnhanceEffect': 'BTL_EnhanceEff',

    'InfoPiece': refset_item,
    'InfoPiece1': refset_item,
    'InfoPiece2': refset_item,
    'InfoPiece3': refset_item,
    'InfoPiece4': refset_item,
    'Item': refset_item,
    'Item1': refset_item,
    'Item2': refset_item,
    'Item3': refset_item,
    'Item4': refset_item,
    'Item5': refset_item,
    'Item6': refset_item,
    'Item7': refset_item,
    'Item01': refset_item,
    'Item02': refset_item,
    'Item03': refset_item,
    'Item04': refset_item,
    'Item05': refset_item,
    'Item06': refset_item,
    'Item07': refset_item,
    'Item08': refset_item,
    'Item09': refset_item,
    'Item10': refset_item,
    'ItemID': refset_item,
    'ItemID1': refset_item,
    'ItemID2': refset_item,
    'ItemID3': refset_item,
    'ItemID4': refset_item,
    'ItemID5': refset_item,
    'ItemID6': refset_item,
    'ItemID7': refset_item,
    'ItemID8': refset_item,
    'ItemId1': refset_item,
    'ItemId2': refset_item,
    'ItemId3': refset_item,
    'ItemId4': refset_item,
    'ItemId5': refset_item,
    'ItemId6': refset_item,
    'ItemId7': refset_item,
    'ItemId8': refset_item,
    'ItemId9': refset_item,
    'ItemId10': refset_item,
    'SetItem1': refset_item,
    'SetItem2': refset_item,
    'SetItem3': refset_item,
    'SetItem4': refset_item,
    'SetItem5': refset_item,
    'SetItem6': refset_item,
    'SetItem7': refset_item,
    'SetItem8': refset_item,
    'SetItem9': refset_item,
    'SetItem10': refset_item,
    'ShopItem1': refset_item,
    'ShopItem2': refset_item,
    'ShopItem3': refset_item,
    'ShopItem4': refset_item,
    'ShopItem5': refset_item,
    'ShopItem6': refset_item,
    'ShopItem7': refset_item,
    'ShopItem8': refset_item,
    'ShopItem9': refset_item,
    'ShopItem10': refset_item,
    'ShopItem11': refset_item,
    'ShopItem12': refset_item,
    'ShopItem13': refset_item,
    'ShopItem14': refset_item,
    'ShopItem15': refset_item,
    'ShopItem16': refset_item,
    'ShopItem17': refset_item,
    'ShopItem18': refset_item,
    'ShopItem19': refset_item,
    'ShopItem20': refset_item,

    'NPCID': refset_npc,
    'NpcID': refset_npc,
    'NpcID1': refset_npc,
    'NpcID2': refset_npc,
    'NpcID3': refset_npc,
    'NpcID4': refset_npc,
    'NpcID5': refset_npc,
    'NpcID6': refset_npc,

    'PcID': refset_pc,

    'QuestID': refset_quest,

    'Reaction': 'BTL_Reaction',

    'ScenarioFlag': 'SYS_ScenarioFlag',

    'TalentID': refset_talent,

    'field_E416DB96': '90A6221A',
}

# List of table-specific fields which are ID references to other tables.
table_xrefs = {
    'BTL_Arts_Chain_Set': {'UseTalent': refset_talent,
                           'UseChr': refset_pc,
                           'ChainArts': refset_arts_pc},
    'BTL_Arts_En': {'StateName': 'BTL_MotionState',
                    'StateName2': 'BTL_MotionState'},
    'BTL_Arts_PC': {'StateName': 'BTL_MotionState',
                    'StateName2': 'BTL_MotionState',
                    'field_C401CF1F': 'BTL_Achievement'},
    'BTL_AutoSetAccessory': {'Talent01': refset_item,
                             'Talent02': refset_item,
                             'Talent03': refset_item,
                             'Talent04': refset_item,
                             'Talent05': refset_item,
                             'Talent06': refset_item,
                             'Talent07': refset_item,
                             'Talent08': refset_item,
                             'Talent09': refset_item,
                             'Talent10': refset_item,
                             'Talent11': refset_item,
                             'Talent12': refset_item,
                             'Talent13': refset_item,
                             'Talent14': refset_item,
                             'Talent15': refset_item,
                             'Talent16': refset_item,
                             'Talent17': refset_item,
                             'Talent18': refset_item,
                             'Talent19': refset_item,
                             'Talent20': refset_item,
                             'Talent21': refset_item,
                             'Talent22': refset_item,
                             'Talent23': refset_item,
                             'Talent24': refset_item,
                             'Talent25': refset_item,
                             'Talent26': refset_item,
                             'Talent27': refset_item,
                             'Talent28': refset_item,
                             'Talent29': refset_item,
                             'Talent30': refset_item,
                             'Talent31': refset_item},
    'BTL_AutoSetArts': {'Talent01': refset_arts_pc,
                        'Talent02': refset_arts_pc,
                        'Talent03': refset_arts_pc,
                        'Talent04': refset_arts_pc,
                        'Talent05': refset_arts_pc,
                        'Talent06': refset_arts_pc,
                        'Talent07': refset_arts_pc,
                        'Talent08': refset_arts_pc,
                        'Talent09': refset_arts_pc,
                        'Talent10': refset_arts_pc,
                        'Talent11': refset_arts_pc,
                        'Talent12': refset_arts_pc,
                        'Talent13': refset_arts_pc,
                        'Talent14': refset_arts_pc,
                        'Talent15': refset_arts_pc,
                        'Talent16': refset_arts_pc,
                        'Talent17': refset_arts_pc,
                        'Talent18': refset_arts_pc,
                        'Talent19': refset_arts_pc,
                        'Talent20': refset_arts_pc,
                        'Talent21': refset_arts_pc,
                        'Talent22': refset_arts_pc,
                        'Talent23': refset_arts_pc,
                        'Talent24': refset_arts_pc,
                        'Talent25': refset_arts_pc,
                        'Talent26': refset_arts_pc,
                        'Talent27': refset_arts_pc,
                        'Talent28': refset_arts_pc,
                        'Talent29': refset_arts_pc,
                        'Talent30': refset_arts_pc,
                        'Talent31': refset_arts_pc},
    'BTL_AutoSetGem': {'Talent01': refset_item,
                       'Talent02': refset_item,
                       'Talent03': refset_item,
                       'Talent04': refset_item,
                       'Talent05': refset_item,
                       'Talent06': refset_item,
                       'Talent07': refset_item,
                       'Talent08': refset_item,
                       'Talent09': refset_item,
                       'Talent10': refset_item,
                       'Talent11': refset_item,
                       'Talent12': refset_item,
                       'Talent13': refset_item,
                       'Talent14': refset_item,
                       'Talent15': refset_item,
                       'Talent16': refset_item,
                       'Talent17': refset_item,
                       'Talent18': refset_item,
                       'Talent19': refset_item,
                       'Talent20': refset_item,
                       'Talent21': refset_item,
                       'Talent22': refset_item,
                       'Talent23': refset_item,
                       'Talent24': refset_item,
                       'Talent25': refset_item,
                       'Talent26': refset_item,
                       'Talent27': refset_item,
                       'Talent28': refset_item,
                       'Talent29': refset_item,
                       'Talent30': refset_item,
                       'Talent31': refset_item},
    'BTL_AutoSetSkill': {'Talent01': refset_skill,
                         'Talent02': refset_skill,
                         'Talent03': refset_skill,
                         'Talent04': refset_skill,
                         'Talent05': refset_skill,
                         'Talent06': refset_skill,
                         'Talent07': refset_skill,
                         'Talent08': refset_skill,
                         'Talent09': refset_skill,
                         'Talent10': refset_skill,
                         'Talent11': refset_skill,
                         'Talent12': refset_skill,
                         'Talent13': refset_skill,
                         'Talent14': refset_skill,
                         'Talent15': refset_skill,
                         'Talent16': refset_skill,
                         'Talent17': refset_skill,
                         'Talent18': refset_skill,
                         'Talent19': refset_skill,
                         'Talent20': refset_skill,
                         'Talent21': refset_skill,
                         'Talent22': refset_skill,
                         'Talent23': refset_skill,
                         'Talent24': refset_skill,
                         'Talent25': refset_skill,
                         'Talent26': refset_skill,
                         'Talent27': refset_skill,
                         'Talent28': refset_skill,
                         'Talent29': refset_skill,
                         'Talent30': refset_skill,
                         'Talent31': refset_skill},
    'BTL_Combo': {'PreCombo': 'BTL_Combo'},
    'BTL_Enemy': {'Resource': 'BTL_EnRsc',
                  'EnemyFamily': 'BTL_EnFamily',
                  'Stance': 'BTL_Stance',
                  'AutoSlot0': refset_arts_en,
                  'AutoSlot1': refset_arts_en,
                  'AutoSlot2': refset_arts_en,
                  'ArtsSlot0': refset_arts_en,
                  'ArtsSlot1': refset_arts_en,
                  'ArtsSlot2': refset_arts_en,
                  'ArtsSlot3': refset_arts_en,
                  'ArtsSlot4': refset_arts_en,
                  'ArtsSlot5': refset_arts_en,
                  'ArtsSlot6': refset_arts_en,
                  'ArtsSlot7': refset_arts_en,
                  'ArtsSlot8': refset_arts_en,
                  'ArtsSlot9': refset_arts_en,
                  'ArtsSlot10': refset_arts_en,
                  'ArtsSlot11': refset_arts_en,
                  'ArtsSlot12': refset_arts_en,
                  'ArtsSlot13': refset_arts_en,
                  'ArtsSlot14': refset_arts_en,
                  'ArtsSlot15': refset_arts_en,
                  'RageStance': 'BTL_Stance'},
    'BTL_Skill_PC': {'UseTalent': refset_talent,
                     'UseChr': refset_pc},
    'BTL_Talent': {'TalentAptitude1': 'BTL_TalentAptitude',
                   'TalentAptitude2': 'BTL_TalentAptitude',
                   'TalentAptitude3': 'BTL_TalentAptitude',
                   'TalentAptitude4': 'BTL_TalentAptitude',
                   'TalentAptitude5': 'BTL_TalentAptitude',
                   'TalentAptitude6': 'BTL_TalentAptitude'},
    'EVT_HeroEquip': {'pc': refset_pc},
    'FLD_ConditionClassLv': {'ClassID': refset_talent},
    'FLD_NpcList': {'Resource1': 'FLD_NpcResource',
                    'Resource2': 'FLD_NpcResource',
                    'Resource3': 'FLD_NpcResource',
                    'Resource4': 'FLD_NpcResource'},
    'FLD_RelationColony': {'field_6E741E84': 'FLD_ColonyList',
                           'field_32A30DD7': 'FLD_ColonyList'},
    'MNU_DlcGift': {'vol_id': '5CD15665',
                    'contents_id': 'DA526616'},
    'MNU_MapInfoFile': {'top_id': 'MNU_MapInfo'},
    'MNU_ShopList': {'TableID': 'MNU_ShopTable'},
    'MNU_UroSkillList': {'SkillID': refset_skill,
                         'UroBodyID': 'CHR_UroBody'},
    'QST_List': {'StartPurpose': 'QST_Purpose'},
    'QST_Purpose': {'TaskID': 'QST_Task',
                    'NextPurposeA': 'QST_Purpose',
                    'NextPurposeB': 'QST_Purpose'},
    'QST_TaskCollect': {'TargetID': refset_item},
    'QST_TaskTalk': {'TargetID': refset_npc},
    'SYS_TutorialEnemyInfo': {'field_10FF2123': refset_enemy,
                              'field_1A391DEB': refset_enemy,
                              'field_032170A4': refset_enemy},
    '02E2BD0D': {'affType': '76D0D7D9',
                 'field_224F1DF3': '7A517BD1',
                 'CollectionID': 'FLD_AffCollection'},
    '03B52788': {'Leader': refset_pc,
                 'Party': 'F9173812'},  # Tutorial battle list
    '0B368E78': {'EffectCondition': refset_condition,
                 'SeCondition': refset_condition},
    '152F4D70': {'field_791E2B72': 'C6B4111D'},  # see around v1.1.0:1b7cac
    '1623B3A0': {'ContentsID': 'DA526616'},
    '23EE284B': {'linkID': refset_event,
                 'linkCondition': 'FLD_ConditionList'},
    '25B62687': {'linkID': refset_event,
                 'linkCondition': 'FLD_ConditionList'},
    'BB0F57A4': {'linkID': refset_event,
                 'linkCondition': 'FLD_ConditionList'},
    '5B1D40C4': {'linkID': refset_event,
                 'linkCondition': 'FLD_ConditionList'},
    '2521C473': {'field_C1781370': 'BTL_Enemy',  # enemy data
                 'field_C6717CFE': '152F4D70',  # guessed from UM drops and 152F4D70->C6B4111D link
                 'field_42284E7E': refset_arts_pc,  # blue mage art learned 
                 'field_B49D11C4': refset_skill},  # blue mage skill learned
    '268AE713': {'affType': '76D0D7D9'},
    '39D667D1': {'Talent': refset_talent},
    '4DA4962C': {'NPC': refset_npc},
    '55C603C7': {'affType': '76D0D7D9'},
    '5A6A68B2': {'PC1': refset_pc,
                 'PC2': refset_pc},
    '5B1907A1': {'TargetID1': refset_npc,
                 'TargetID2': refset_npc,
                 'TargetID3': refset_npc,
                 'TargetID4': refset_npc,
                 'TargetID5': refset_npc,
                 'TargetID6': refset_npc,
                 'TargetID7': refset_npc,
                 'TargetID8': refset_npc},
    '5F654D94': {'Talent': refset_talent,
                 'SkillID': refset_skill},
    '6EC8096C': {'CookName': 'FLD_CookRecipe'},
    '72C56041': {'PC1': refset_pc,
                 'Object1': 'RSC_MapObjList',
                 'PC2': refset_pc,
                 'Object2': 'RSC_MapObjList'},
    '74385681': {'field_F5E05E39': 'FLD_ConditionList',
                 'field_08C0C3DD': refset_quest,
                 'Arts1': refset_arts_pc,
                 'Arts2': refset_arts_pc,
                 'Arts3': refset_arts_pc,
                 'Arts4': refset_arts_pc,
                 'Arts5': refset_arts_pc,
                 'Arts6': refset_arts_pc},
    '76FFBF3F': {'affType': '76D0D7D9'},
    '7A066663': {'TaskID': refset_quest_taskid},
    '949AA63A': {'Reward1': refset_item,
                 'Reward2': refset_item,
                 'Reward3': refset_item,
                 'Reward4': refset_item,
                 'Reward5': refset_item,
                 'Reward6': refset_item,
                 'Reward7': refset_item,
                 'Reward8': refset_item,
                 'Reward9': refset_item,
                 'Reward10': refset_item,
                 'Reward11': refset_item,
                 'Reward12': refset_item,
                 'Reward13': refset_item,
                 'Reward14': refset_item,
                 'Reward15': refset_item,
                 'Reward16': refset_item,
                 'Reward17': refset_item,
                 'Reward18': refset_item,
                 'Reward19': refset_item,
                 'Reward20': refset_item},
    'A3CAD8C7': {'Talent': refset_talent,
                 'arts01': refset_arts_pc,
                 'arts02': refset_arts_pc,
                 'arts03': refset_arts_pc,
                 'arts04': refset_arts_pc,
                 'arts05': refset_arts_pc,
                 'arts06': refset_arts_pc,
                 'field_F93D37D3': refset_arts_pc},
    'A6AAF689': {'ArtsID': refset_arts_pc},
    'B971C420': {'Talent': refset_talent,
                 'ArtsID': (('BTL_Arts_PC', 'E29EF7E9'), )},
    'BF287371': {'affType': '76D0D7D9'},
    'C29E28FD': {'Object1': 'RSC_MapObjList'},
    'D0253D11': {'ChrID': refset_pc,
                 'ClassID': refset_talent,
                 'ArtsID': refset_arts_pc},
    'D327B2BC': {'TaskID': 'QST_Task'},
    'D9B88F26': {'CompBonus1': refset_enhance,
                 'CompBonus2': refset_enhance,
                 'CompBonus3': refset_enhance,
                 'CompBonus4': refset_enhance,
                 'CompBonus5': refset_enhance,
                 'KeyChr1': refset_pc,
                 'KeyChr2': refset_pc,
                 'KeyChr3': refset_pc,
                 'KeyChr4': refset_pc,
                 'KeyChr5': refset_pc,
                 'KeyChr6': refset_pc},
    'DA526616': {'VolID': '5CD15665'},
    'DF81B4D2': {'affType': '76D0D7D9'},
    'E44BEAA2': {'PC': refset_pc},
    'F9173812': {'PC01': refset_pc,
                 'ArtsSet01': 'A3CAD8C7',
                 'PC02': refset_pc,
                 'ArtsSet02': 'A3CAD8C7',
                 'PC03': refset_pc,
                 'ArtsSet03': 'A3CAD8C7',
                 'PC04': refset_pc,
                 'ArtsSet04': 'A3CAD8C7',
                 'PC05': refset_pc,
                 'ArtsSet05': 'A3CAD8C7',
                 'PC06': refset_pc,
                 'ArtsSet06': 'A3CAD8C7'},
}

def add_xref(table, row, field_idx, value, target_table, target_row):
    """Add a cross-reference from table[row][field_idx] to target_table[row]."""
    if value is None:
        if target_table.name in row_name_fields:
            name_idx = target_table.field_index(row_name_fields[target_table.name])
            value = target_table.get(target_row, name_idx)
        else:
            value = ""
        if value == "":
            value = target_table.get(target_row, 0)
    table.set(row, field_idx, value,
              target_table.name, target_table.get(target_row, 0))

    if table.name in row_name_fields:
        name_idx = table.field_index(row_name_fields[table.name])
        row_value = table.get(row, name_idx)
    else:
        row_value = ""
    if row_value == "":
        row_value = table.get(row, 0)
    target_table.addref(target_row, table.name, table.get(row, 0), row_value)


def resolve_field_xrefs(tables, table, field_idx, target):
    """Resolve cross-references in the given table column."""
    if not islistlike(target):
        target = (target,)
    target_tables = target[0]
    if not islistlike(target_tables):
        target_tables = (target_tables,)
    matched = False
    for row in range(table.num_rows):
        value = table.get(row, field_idx)
        if value == 0 or value == '':
            table.set(row, field_idx, '')
        else:
            id = value
            target_table = None
            target_row = None
            for name in target_tables:
                test_table = tables[name]
                test_row = test_table.id_to_row(id)
                if test_row is not None:
                    if target_row is None:
                        target_table = test_table
                        target_row = test_row
                    else:
                        raise ValueError(f'Duplicate ID {id} in table {target_table_name} (reference from {table.name}#{table.get(row, 0)})')
            if target_row is None:
                # Suppress known unamtched cases
                if table.name == 'QST_Purpose' and table.field(field_idx).name.startswith('NextPurpose') and (id == 30000 or id == 30001):
                    pass
                elif table.name == 'QST_TaskTalk' and table.field(field_idx).name == 'TargetID' and re.match(r'^[0-9]+$', id):
                    pass
                else:
                    print(f'Warning: {table.name}[{table.get(row, 0)}].{table.field(field_idx).name} ({id}) not matched', file=sys.stderr)
                continue
            if len(target) > 1:
                target_field = target_table.field_index(target[1])
                value = target_table.get(target_row, target_field)
                if value is None or value == '':
                    value = id
                elif len(target) > 2:
                    if target[2] == 'enhance':
                        for n in (1,2,3):
                            try:
                                param_idx = table.field_index(f'Param{n}')
                                param = table.get(row, param_idx)
                                if isinstance(param, float):
                                    param = f'{param:g}'
                                value = value.replace(f'[ML:EnhanceParam paramtype={n} ]', param)
                            except ValueError:
                                pass
                    elif target[2] == 'urobody_name':
                        target_row += 81
                        value = target_table.get(target_row, target_field)
                    elif target[2] == 'achievement':
                        value = target_table.get(target_row, target_field)
                        idx_type = table.field_index('AchieveType')
                        idx_param1 = table.field_index('Param1')
                        idx_param2 = table.field_index('Param2')
                        type = table.get(row, idx_type)
                        param1 = table.get(row, idx_type)
                        param2 = table.get(row, idx_type)
                        if type <= 7:
                            value += f' ({param1})'
                        elif type != 255:
                            value += f' ({param2})'
                    else:
                        raise ValueError(target[2])
            else: # len(target) > 1
                value = None  # default rules
            add_xref(table, row, field_idx, value, target_table, target_row)


def resolve_xrefs(tables):
    """Resolve all cross-references in the given list of tables."""
    for table_name, fields in text_xrefs.items():
        if table_name == 'FLD_NpcList':
            continue  # force after FLD_NpcResource
        table = tables[table_name]
        for field, target in fields.items():
            resolve_field_xrefs(tables,
                                table, table.field_index(field), target)
    for field, target in text_xrefs['FLD_NpcList'].items():
        resolve_field_xrefs(tables, tables['FLD_NpcList'],
                            tables['FLD_NpcList'].field_index(field), target)
    for name, table in tables.items():
        if name == 'BTL_Achievement':  # Special case for value-dependent refs
            idx_type = table.field_index('AchieveType')
            idx_param1 = table.field_index('Param1')
            for row in range(table.num_rows):
                type = table.get(row, idx_type)
                param1 = table.get(row, idx_param1)
                if type in (9,12):
                    target_table = tables['2521C473']
                elif type in (10,11):
                    target_table = tables['BTL_Arts_PC']
                elif type >= 13 and type <= 17:
                    target_table = tables['BTL_Skill_PC']
                else:
                    target_table = None
                if target_table:
                    target_row = target_table.id_to_row(param1)
                    target_field = target_table.field_index(row_name_fields[target_table.name])
                    value = target_table.get(target_row, target_field)
                    if value == "":
                        value = table.get(row, idx_param1)
                    add_xref(table, row, idx_param1, value,
                             target_table, target_row)
        if name in table_xrefs:
            for field, target in table_xrefs[name].items():
                resolve_field_xrefs(tables,
                                    table, table.field_index(field), target)
        for field, target in field_xrefs.items():
            try:
                field_idx = table.field_index(field)
                resolve_field_xrefs(tables, table, field_idx, target)
            except ValueError:
                pass
        hash_re = re.compile(r'<([0-9A-F]{8})>$')
        for field_idx in range(2, table.num_fields):
            field = table.field(field_idx)
            if field.value_type == BdatValueType.HSTRING:
                for row in range(table.num_rows):
                    value = table.get(row, field_idx)
                    if isinstance(value, str):
                        m = hash_re.match(value)
                        if m:
                            target_table_name, target_row = BdatTable.global_id_lookup(m.group(0))
                            if target_table_name:
                                target_table = tables[target_table_name]
                                add_xref(table, row, field_idx, None,
                                         target_table, target_row)

########################################################################
# Program entry point

def main(argv):
    """Program entry point."""
    parser = argparse.ArgumentParser(
        description='Extract tables from Xenoblade BDAT files.')
    parser.add_argument('-o', '--outdir', metavar='OUTDIR', required=True,
                        help='Path of output directory for table HTML files.')
    parser.add_argument('files', metavar='FILE', nargs='+',
                        help='Paths of BDAT files to read.')
    args = parser.parse_args()

    tables = {}
    for file in args.files:
        bdat = Bdat(file)
        for table in bdat.tables():
            tables[table.name] = table

    if 'BTL_LvRev' in tables:  # XC3 only
        resolve_xrefs(tables)

    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)
    for name, table in tables.items():
        fname = re.sub('[^ -.0-~]', '_', name) + '.html'
        s = table.print()
        with open(os.path.join(args.outdir, fname), 'wb') as f:
            f.write(s.encode('utf-8'))
# end def


if __name__ == '__main__':
    main(sys.argv)
