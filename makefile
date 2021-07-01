SHELL=/bin/bash
run:
	# nohup python hello.py
	# nohup python -m flask run --host=0.0.0.0 --port=80 &
	# run(self, host=None, port=None, debug=None
	source virtualenvwrapper.sh; workon env37; source .env; cd /home/admin/fllog ; python3.7 hello.py
