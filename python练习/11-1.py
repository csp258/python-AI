
path = r"C:\Users\win11\OneDrive\桌面\实验11 文件操作\file.txt"


with open(path, 'r', encoding='utf-8') as file:

    for line in file:
        
        cleaned_line = line.rstrip('\n')
      
        if cleaned_line.startswith('#'):
            continue
   
        count = len(cleaned_line)
    
        print(f"{count}:{cleaned_line}")