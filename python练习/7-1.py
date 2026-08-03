playlist =['爱在西元前','江南','十年','说爱你','海阔天空','暗号']
playlist.append("最后一页")

playlist =[song for song in playlist if "爱" not in song]

if "海阔天空" in playlist:
    print("海阔天空的索引为:",playlist.index("海阔天空"))
else:
    print("不存在海阔天空")
for i in range(len(playlist)):
    if playlist[i] == "十年":
        playlist[i] == "明年今日"

        newplaylist = playlist[1:4]
        print("新列表:",newplaylist)
        print("最终播放列表:",playlist)