# Fastdiff.py: Compare two directories quickly

Fastdiff.py compares two directories to determine if they contain the same files. The files are only compared by size to ensure fast execution.

Just use the following command to compare two directories recursively:
```
fastdiff.py -r dir1 dir2
```

## Install

1. Install Python3 as follows in Ubuntu/Debian Linux:
```
sudo apt install python3
```

2. Download Fastdiff.py and set execute permissions:
```
curl -LJO https://raw.githubusercontent.com/byte-cook/fastdiff/main/fastdiff.py
chmod +x fastdiff.py
```

3. (Optional) Use [opt.py](https://github.com/byte-cook/opt) to install it to the /opt directory:
```
sudo opt.py install fastdiff fastdiff.py
```
