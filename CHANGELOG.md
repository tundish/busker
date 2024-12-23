History
=======

0.22.0
------

* Only emit termination Events when they match verdict.

0.21.0
------

* More robust error handling within compass layout.

0.20.0
------

* Renamed Event attribute `support`.

0.19.0
------

* Add unit test for Event priority.

0.18.0
------

* Add `priority` attribute to Event.

0.17.0
------

* Revert states attribute
* Add puzzles to graph when init table declared.

0.16.0
------

* Implement lightweight puzzle chain as list.
* Add attribute `states` to gathered puzzles.

0.15.0
------

* Introduced proofer module.
* Add attributes `sketch`, `aspect`, `revert` to gathered puzzles.
* Allow a staged puzzle to chain an event to itself.
* Add 'done' parameter to Stager.terminate method.
* Refactor Event type.

0.14.0
------

* Utilize Events across puzzle chain.
* `Stager.terminate` generates Events from table array.

0.13.0
------

* Fix realm of test data

0.12.0
------

* Fix Stager.active property when there is no puzzle chain.
* Add Stager.puzzles property.
* Update test data to assist rotu development.

0.11.0
------

* Completed dev and test of stage graph utility.

0.10.0
------

* Improvements to `Stager.gather_puzzle`.

0.9.0
-----

* Added stager module.

0.8.0
-----

* Refactored several classes and modules.
* Better counting by Witness.

0.7.0
-----

* Interactive tab fully working.
* Hosting workflow robust.
* Tested on Windows (Python 3.12).

0.6.0
-----

+ Hosting tab working fully.
+ Basic implementation of Interactive transcript.

0.5.0
-----

Rerelease without stray venv directories.

0.4.0
-----

Busker mostly de-risked now.

+ Multiprocessing IPC in place to pass progress of runners.
+ Basic GUI layout established.
+ Connect to server displays About info.
+ Virtual environment builds correctly.

0.3.0
-----

+ Add GUI module.
