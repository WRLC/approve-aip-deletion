# approve-aip-deletion

Python script using Selenium to automate approval of package deletion requests in Archivematica's Storage Service.

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

```
cp settings.template.py settings.py
```

```
python3 main.py '<reason for deletion>'
```