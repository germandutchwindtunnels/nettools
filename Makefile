test: Cisco.py OutputLog.py PortConfigGui.py portconfig.py NewGui.pyw
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods Cisco.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods OutputLog.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member PortConfigGui.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member portconfig.py
	pylint --disable=bad-whitespace,invalid-name,too-many-public-methods,too-few-public-methods,too-many-instance-attributes,no-init,no-name-in-module,no-member NewGui.pyw
	python -m py_compile Cisco.py
	python -m py_compile OutputLog.py
	python -m py_compile portconfig.py
	python -m py_compile PortConfigGui.py
	python -m py_compile NewGui.pyw

