# ckanext-invalid-uris
CKAN extension to detect invalid URIs

# How to use
execute below to enqueue the task to the background job. 

`ckan -c /app/ckan/default/ckan.ini register-uri-validation-job`

Available options for above command are
```
Options:
  -t, --type TEXT           Optional. Type of the job, default: 'created'.
                            
                            Possible values:
                            
                            'created' => filter package by created date within
                            last 24h
                            
                            'updated' => filter package by updated/modified
                            date within last 24h
                            
                            'all' => get all metadata

  -p, --package_types TEXT  Optional. List of the package types, comma
                            separated, default: 'dataset dataservice'

  -v, --validator TEXT      Optional. The name of the uri validator, default:
                            'qdes_uri_validator'
```

example to validate created package within last 24h.

`ckan -c /app/ckan/default/ckan.ini register-uri-validation-job -t 'created' -p 'dataset dataservice' -v 'qdes_uri_validator'`

To execute job manually: `ckan -c /app/ckan/default/ckan.ini jobs worker`
