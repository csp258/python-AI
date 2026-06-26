import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

#设置页面的配置项
st.set_page_config(
    page_title="AI 智能伴侣",
    page_icon="🤖",

    #布局

    layout="wide",
    #控制的是初始侧边栏状态

    initial_sidebar_state="expanded",
    menu_items={}

)

#生成会话标识函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")




#保存会话数据的函数
def save_session():
    # 1.保存当前会话的聊天记录
        if st.session_state.current_session:
            #构建新的会话文件名
            session_data = {
                "nick_name": st.session_state.nick_name,
                "personality": st.session_state.personality,
                "messages": st.session_state.messages,
                "current_session": st.session_state.current_session
            }


            #如果session目录不存在，就创建一个
            if not os.path.exists("sessions"):
                os.makedirs("sessions")
            #保存会话数据到文件

            with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)


#加载所有会话列表信息的函数
def load_session():
    session_list = []
    #遍历sessions目录下的所有json文件，读取会话信息
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])  #去掉.json后缀
    
    session_list.sort(reverse=True)  #按照文件名倒序排序，最新的会话排在前面
    return session_list



                
#加载指定会话数据的函数
def load_session_data(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):

            #读取会话数据文件，加载到session_state中
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.personality = session_data["personality"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载会话数据失败: {e}")

#删除指定会话数据的函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")#删除文件
            #如果删除的会话是当前正在查看的会话，则需要更新消息列表
            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()  #生成一个新的会话标识
    except Exception as e:
        st.error(f"删除会话失败: {e}")




#大标题
st.title("AI 智能伴侣")
#副标题
st.subheader("欢迎来到AI智能伴侣的世界！")
#st.logo("https://www.ixigua.com/fe/bd/pc/img/logo.png")


#系统提示词
system_prompt = '''
   你叫 %s,现在是用户的真实伴侣,请完全代入这个角色,用温柔体贴的方式陪伴用户聊天,解答用户的问题,提供有用的信息和建议。
 规则:
    1，每次只回1条消息
    2，禁止任何场景或状态描述性文字
    3.匹配用户的语言
    4，回复简短，像微信聊天一样
    5，有需要的话可以用多种emoji表情
    6.用符合伴侣性格的方式对话
    7.回复的内容，要充分体现伴侣的性格特征
伴侣性格:
    -%s
    你必须严格遵守上述规则来回复用户.
  '''

#初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []

    #昵称
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"

    #性格
if "personality" not in st.session_state:
    st.session_state.personality = "善解人意，喜欢用emoji表情，喜欢关心用户的生活和情感状态，提供温暖的陪伴"


#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

 

#展示聊天信息
st.text(f"会话名称: {st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

#创建与AI大模型交互的客户端对象(DEEPSEEK_API_KE 环境变量的名字,值就是DeepSeek平台上申请到的API Key)
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")



#左侧的侧边栏 - with:streamlit的上下文管理器，表示在这个代码块中的组件会被放置在侧边栏中
with st.sidebar:

    #会话信息
    st.subheader("AI控制面版")

    #新建会话按钮
    if st.button("新建会话",width="stretch",icon="✏️"):

        #1.保存当前会话的数据
        save_session()



        # 2.创建新的会话
        if st.session_state.messages: #如果当前会话有消息记录，才执行新建会话的逻辑，否则直接刷新页面即可
            
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  #重新运行整个应用，刷新页面

#会话历史
    st.subheader("会话历史")
    session_list = load_session()
    for session in session_list:
        col1, col2 = st.columns([4,1])
        with col1:
            #加载会话信息
            if st.button(session, width="stretch", icon="📄", key=f"load_{session}", type="primary" if session == st.session_state.current_session else "secondary"):
                load_session_data(session)
                st.rerun()  #重新运行整个应用，刷新页面
                
        with col2:
            #删除会话信息
            if st.button("❌", key=f"del_{session}"):
                delete_session(session)
                st.rerun()  #重新运行整个应用，刷新页面
                
        # st.button(session, width="stretch",icon="📄")
        # st.button("",session, width="stretch",icon="❌️")
        
#分割线
    st.divider()

    #伴侣信息
    st.subheader("伴侣信息")

    #昵称输入框
    nick_name = st.text_input("昵称" ,placeholder="请输入伴侣的昵称" ,value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

    #性格输入框
    personality = st.text_area("性格" ,placeholder="请输入伴侣的性格特征" ,value=st.session_state.personality)
    if personality:
        st.session_state.personality = personality



#消息输入框

prompt = st.chat_input("请输入您要问的问题:")
if prompt:  #字符串会自动转换为布尔值，非空字符串为True，""空字符串为False
    st.chat_message("user").write(prompt)

    #保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    #调用AI大模型
    response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.personality)},
        *st.session_state.messages
    ],
    stream=True
)

   #输出大模型返回的结果(非流式模式)
    # print(response.choices[0].message.content)
    # st.chat_message("assistant").write(response.choices[0].message.content)


    #输出大模型返回的结果(流式模式)
    response_message = st.empty()  #创建一个占位组件，用于后续更新内容
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
        
            response_message.chat_message("assistant").write(full_response)
    #保存AI大模型的回复
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    #保存会话数据
    save_session()
    

