import os
import re
import shutil
import random
import string
import colorama
import shlex
import xml.etree.ElementTree as ET

def update_encryption_key(content):
    key = ''.join(random.choices(string.ascii_letters, k=16))
    content = re.sub(re.escape('public static byte[] key = Encoding.UTF8.GetBytes("DepthSecurity");'), f'public static byte[] key = Encoding.UTF8.GetBytes("{key}");', content)
    return content, key

def update_writetofile(content):
    content = re.sub(re.escape('bool shouldWriteToFile = false;'), 'bool shouldWriteToFile = true;', content)
    return content

def update_hostname(content, hostname):
    content = re.sub(r'TESTVM', hostname, content)
    return content

def update_resource_references(content, num_chunks):
    resources = ''
    for i in range(num_chunks):
        resources += (f"chunks.Add(Resources.FileChunk{i});\n            ")
    content = re.sub(re.escape(f"chunks.Add(Resources.FileChunk1);"), resources, content)
    return content

def randomize_assembly_name(csproj_filepath, new_name):
    
    # Parse the .csproj XML file
    tree = ET.parse(csproj_filepath)
    root = tree.getroot()

    property_group = root.find('PropertyGroup')
    if property_group is not None:
        assembly_name_element = ET.SubElement(property_group, 'AssemblyName')

    # Update the AssemblyName to the new random name
    assembly_name_element.text = new_name
    
    # Write changes back to the .csproj file
    tree.write(csproj_filepath, encoding="utf-8", xml_declaration=True)

    return new_name
        
def run(hostname, num_chunks, args, writetofile):
    # Input and output directories
    input_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
    output_dir =  os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp"))

    # Copy unobfuscated source to preserve it
    if(os.path.exists(output_dir)):
        shutil.rmtree(output_dir)
        shutil.copytree(input_dir, output_dir)
    else:
        shutil.copytree(input_dir, output_dir)

    csproj_filepath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../temp/PositiveIntent/PositiveIntent.csproj"))
    assembly_name = randomize_assembly_name(csproj_filepath, ''.join(random.choices(string.ascii_letters, k=8)))
    
    # Loop over source files and update user-supplied hostname/args/writetofile options as well as resource file references
    for root, dirs, files in os.walk(output_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in ("bin", "obj", "Resources", "Properties")]
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith('.cs'):
                with open(file_path, 'r+', encoding='utf-8') as file:
                    content = file.read()
                    if(writetofile):
                        content = update_writetofile(content)
                    if(args):
                        content = update_arguments(args, content)
                    if("RC4" in file_name):
                        content, key = update_encryption_key(content)
                    content = update_hostname(content, hostname)
                    content = update_resource_references(content, num_chunks)
                    file.seek(0)
                    file.write(content)
                    file.truncate()
    return assembly_name, key
