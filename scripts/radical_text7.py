"""Unicode display transcription of PDF33-34. IDs and stroke groups stay source-backed."""
MAIN='一 丨 丿 丶 乛 十 厂 匚 卜 冂 八 人 勹 儿 匕 几 亠 冫 冖 凵 卩 刀 力 又 厶 廴 干 工 土 艹 寸 廾 大 尢 弋 小 口 囗 山 巾 彳 彡 夕 夂 丬 广 门 宀 辶 彐 尸 己 弓 子 屮 女 飞 马 幺 巛 王 无 韦 木 支 犬 歹 车 牙 戈 比 瓦 止 攴 日 贝 水 见 牛 手 气 毛 长 片 斤 爪 父 月 氏 欠 风 殳 文 方 火 斗 户 心 毋 示 甘 石 龙 业 目 田 罒 皿 生 矢 禾 白 瓜 鸟 疒 立 穴 疋 皮 癶 矛 耒 老 耳 臣 覀 而 页 至 虍 虫 肉 缶 舌 竹 臼 自 血 舟 色 齐 衣 羊 米 聿 艮 羽 糸 麦 走 赤 豆 酉 辰 豕 卤 里 足 邑 身 釆 谷 豸 龟 角 言 辛 青 龺 雨 非 齿 黾 隹 阜 金 鱼 隶 革 面 韭 骨 香 鬼 食 音 首 髟 鬲 鬥 高 黄 麻 鹿 鼎 黑 黍 鼓 鼠 鼻 龠'.split()
ALIASES='⺊ 刂 亻 ⺁ 入 ⺈ ⺆ ⺇ 丷 讠 阝 阝 㔾 士 扌 兀 ⺌ 犭 饣 氵 忄 ⺕ 已 巳 ⺍ 彑 纟 耂 朩 旡 ⺗ ⺜ 冃 龵 攵 尣 爫 灬 礻 肀 爿 玉 歺 氺 钅 衤 ⺻ ⺪ 母 ⺶ ⺷ 聿 艸 糹 镸 車 貝 見 ⻊ 辵 長 虎 門 飠 頁 風 韋 飛 馬 麥 鹵 鳥 魚 黽 齊 齒 龍 龜'.split()
NAMES={'艹':'草字头','氵':'三点水','扌':'提手旁','亻':'单人旁','讠':'言字旁','忄':'竖心旁','辶':'走之旁','犭':'反犬旁','纟':'绞丝旁','钅':'金字旁','饣':'食字旁','礻':'示字旁','衤':'衣字旁','宀':'宝盖头','广':'广字旁','灬':'四点底','刂':'立刀旁','阝':'耳旁','⺌':'小字头','⺍':'三点头','⺗':'心字底','耂':'老字头','⺕':'彐附形','龵':'手附形','⺻':'聿附形','⺪':'疋附形'}
def annotate(forms):
 assert len(MAIN)==201 and len(ALIASES)==78
 aliases=iter(ALIASES)
 for f in forms:
  label=next(aliases) if f['alias'] else MAIN[f['number']-1]
  hint=('左耳旁' if f['number']==175 else '右耳旁') if label=='阝' else NAMES.get(label,label+'部')
  f['label']=label;f['hint']=hint
 return forms
