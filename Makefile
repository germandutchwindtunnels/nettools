test: Cisco.py OutputLog.py PortConfigGui.py portconfig.py NewGui.pyw AutoUpdate.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods Cisco.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-member OutputLog.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member PortConfigGui.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member portconfig.py
	pylint --disable=bad-whitespace,invalid-name,too-many-public-methods,too-few-public-methods,too-many-instance-attributes,no-init,no-name-in-module,no-member NewGui.pyw
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member AutoUpdate.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member ip_trace.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member network_graph.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member network_overview.py
	pylint --disable=mixed-indentation,line-too-long,bad-whitespace,anomalous-backslash-in-string,invalid-name,too-many-public-methods,no-name-in-module,no-member remote_span.py
	python -m py_compile Cisco.py
	python -m py_compile OutputLog.py
	python -m py_compile portconfig.py
	python -m py_compile PortConfigGui.py
	python -m py_compile NewGui.pyw
	python -m py_compile AutoUpdate.py
	python -m py_compile ip_trace.py
	python -m py_compile network_overview.py
	python -m py_compile network_graph.py
	python -m py_compile remote_span.py

