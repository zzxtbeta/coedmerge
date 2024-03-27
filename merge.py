import gradio as gr
import os
import openai
import difflib
import sys

# client = OpenAI(api_key="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")
openai.api_type = "azure"
openai.api_base =  "https://12345678.openai.azure.com/"
openai.api_version = "2023-08-01-preview"
openai.api_key = "ed9b1ce76dc14fcf875b93dc8c852f51"


# 新钩子函数取值

conflict_directory = sys.argv[1]
# print("conflict_directory：", conflict_directory)
file_names = []
file_contents = []

for filename in os.listdir(conflict_directory):
    file_path = os.path.join(conflict_directory, filename)
    # print("------------file_path--------------:", file_path)
    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:  # 指定 'utf-8' 编码
            file_names.append(filename)
            file_contents.append(file.read())

file_count = len(file_names)
print("冲突文件数量:", file_count)
  
current_index = -1  # 记录 file_contents 的当前索引

def resolve_conflict(code, file_type):
    global current_index
    response = openai.ChatCompletion.create(
        engine="gpt3501",
        messages=[
            {"role": "system", "content": f"""
            你是一名经验丰富的程序员，以下是由两个不同版本{file_type}代码进行代码合并后得到的一份待处理冲突代码。其中"<<<<<<< HEAD"表示代码冲突的起始标志，">>>>>>> branch-b"表示代码冲突的结束标志，
            夹在起始标志和结束标志中间的"======="用于分隔冲突部分两个不同分支的代码，请根据冲突标志分析其中代码冲突的部分，依据整体代码逻辑解决冲突，然后消去冲突标志，注意输出合并结果时请勿省略长代码段和注释，请勿生成给定代码中不存在的代码，保证输出代码的完整性和正确性，只输出合并后代码，不输出其他文字分析内容
            """},
            {"role": "user", "content": f"{code}"},],
    )
    return response.choices[0].message.content.strip(),""

def resolve_conflict_and_analysis(code, file_type):
    global current_index
    response = openai.ChatCompletion.create(
        engine="gpt3501",
        temperature=0.5,
        messages=[
            {"role": "system", "content": f"""
            你是一名经验丰富的程序员，以下是由两个不同版本{file_type}代码进行代码合并后得到的一份待处理冲突代码。其中"<<<<<<< HEAD"表示代码冲突的起始标志，">>>>>>> branch-b"表示代码冲突的结束标志，
            夹在起始标志和结束标志中间的"======="用于分隔冲突部分两个不同分支的代码，请根据冲突标志分析其中代码冲突的部分，依据整体代码逻辑解决冲突，消去冲突标志，注意输出合并结果时请勿省略长代码段和注释，请勿生成给定代码中不存在的代码，保证输出代码的完整性和正确性，
            先输出合并后代码，再用中文解释你这么合并的原因，代码和解释两部分之间用"####################"分隔开。
            """},
            {"role": "user", "content": f"{code}"},]
    )
    res = response.choices[0].message.content
    print("res:",res)
    sections = res.split("####################")
    merged_code = sections[0].strip()
    conflict_analysis = sections[1].strip()

    return merged_code, conflict_analysis

def submit_result(file_name, merged_code):
    with open(file_name, "w") as file:
        file.write(merged_code)
    return f"{file_name}已更新！"

def next_conflict():
    global current_index
    if current_index < len(file_contents)-1:
        current_index += 1
        if '.' not in file_names[current_index]:
            file_type = ""
        else:
            file_type = file_names[current_index].split('.')[-1]
    else:
        # 如果所有冲突都处理完毕，退出 Gradio
        return "所有冲突浏览完毕", "所有冲突已处理", "","",""
    return file_names[current_index],file_contents[current_index], file_type, "",""

def previous_conflict():
    global current_index
    if current_index > 0:
        current_index -= 1
        if '.' not in file_names[current_index]:
            file_type = ""
        else:
            file_type = file_names[current_index].split('.')[-1]
    else:
        return file_names[current_index],file_contents[current_index], "", "","当前已经是第一条冲突！"
    return file_names[current_index],file_contents[current_index], file_type, "",""

def merge_and_submit_all_conflicts():
    merge_results = []
    for i in range(len(file_names)):
        conflict_code = file_contents[i]
        file_type = ""
        if '.' in file_names[i]:
            file_type = file_names[i].split('.')[-1]
        merged_code, _ = resolve_conflict(conflict_code, file_type)
        merge_results.append(submit_result(file_names[i], merged_code))
    return merge_results


css = """

.merge_button_class {
    width: 50px;
    height: 5px; /* 
    # margin: 0px 50px;
}

.next_button_class {
    width: 100px;高度为40px */
    # margin: 0px 50px;
}


"""

with gr.Blocks(css=css) as app:
    gr.Markdown(f"本次分支合并冲突文件数量: {file_count}个")
    with gr.Row():
        current_file_name = gr.TextArea(label="当前冲突文件名:")
        current_file_type = gr.TextArea(label="文件类型:")
    with gr.Row():
        conflict_code_input = gr.TextArea(label="冲突代码文本")
        merged_code_output = gr.TextArea(label="合并后的代码文本")
    with gr.Column():
        conflict_analysis_output = gr.TextArea(label="冲突解决分析")
        merge_button = gr.Button("生成合并代码")
        merge_analysis_button = gr.Button("生成合并代码和分析(beta)")
        submit_button = gr.Button("提交合并结果")
        merge_and_submit_button = gr.Button("一键生成合并结果并提交")  # 新增的按钮
    with gr.Row():
        previous_button = gr.Button("上一条冲突")
        next_button = gr.Button("下一条冲突")

    merge_button.click(fn=resolve_conflict, inputs=[conflict_code_input, current_file_type], outputs=[merged_code_output,conflict_analysis_output])
    merge_analysis_button.click(fn=resolve_conflict_and_analysis, inputs=[conflict_code_input, current_file_type], outputs=[merged_code_output,conflict_analysis_output])
    submit_button.click(fn=submit_result, inputs=[current_file_name, merged_code_output], outputs=current_file_name)
    merge_and_submit_button.click(fn=merge_and_submit_all_conflicts, outputs=current_file_name)

    next_button.click(fn=next_conflict, outputs=[current_file_name, conflict_code_input, current_file_type, merged_code_output, conflict_analysis_output])
    previous_button.click(fn=previous_conflict, outputs=[current_file_name, conflict_code_input, current_file_type, merged_code_output, conflict_analysis_output])

# Gradio 界面启动时自动加载第一个冲突
first_file_name, first_conflict_code,  file_type, _, _ = next_conflict()
current_file_name.value = first_file_name
conflict_code_input.value = first_conflict_code
current_file_type.value = file_type


app.launch()
