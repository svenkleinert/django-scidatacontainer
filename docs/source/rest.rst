REST API
========

The data storage server provides a browser interface as well as a `REST API <https://en.wikipedia.org/wiki/Representational_state_transfer>`_. A user account is required to access the server and get an API key for the REST API via the browser interface.


Container Upload
----------------

:Method: POST
:URL: http://<server>/api/datasets/
:Content: Container files
:Header: Authorization: Token <key>

Response:

.. csv-table:: 
	:header: HTTP return code, Description, Returned content

	``201 Created``, Successful container upload
	``400 Bad Request``, Existing static dataset with same ``hash`` and ``containerType``, JSON object
	``400 Bad Request``, Malformed or invalid container
	``403 Forbidden``, Unauthorized access
	``409 Conflict``, Existing completed dataset with same UUID
	``415 Unsupported``, Invalid container format
	``500 Server Error``, Internal server error


Container Download
------------------

:Method: GET
:URL: http://<server>/api/datasets/<uuid>/download/
:Header: Authorization: Token <key>

Response:

.. csv-table:: 
	:header: HTTP return code, Description, Returned content

	``200 OK``, Success, Data container
	``204 No Content``, Dataset deleted
	``301 Moved Permanently``, Dataset replaced, Last replacement of container
	``403 Forbidden``, Unauthorized access
	``404 Not Found``, No dataset available
	``500 Server Error``, Internal server error
