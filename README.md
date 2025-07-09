### backlog

url_checker
https://pin-up-global.slack.com/archives/C03NN429U2X/p1751869898043659


-----

## `project_collector` collects selected project code in one Markdown file.

The script accepts the following parameters:

* Path to the logging directory (required)
* `-l`, `--language` -- project language (optional)
* `-h`, `--help` -- help (optional)

### Getting started

* Create a directory for project logging. For example, `~/ProjectsLog/MyApplication`
* Copy and rename the files `config.ini.example` and `files.txt.example` into `~/ProjectsLog/MyApplication` :
```shell
cp config.ini.example ~/ProjectsLog/MyApplication/config.ini
cp files.txt.example ~/ProjectsLog/MyApplication/files.txt
```
* Edit these files to suit your needs
* Start logging the project:

```shell
./project_collector.py ~/ProjectsLog/MyApplication
```

You're done :)
