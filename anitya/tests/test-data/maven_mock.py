#!/usr/bin/python
import json
returned_data = [{"groupId":"ai.h2o","artifactId":"deepwater-backend-api","version":"1.0.3"},
                 {"groupId":"ai.h2o","artifactId":"sparkling-water-core_2.11","version":"2.0.6"}]
print(json.dumps(returned_data))
