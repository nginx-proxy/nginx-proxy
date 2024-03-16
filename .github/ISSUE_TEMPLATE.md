# ⚠️ PLEASE READ ⚠️

## Questions or Features

If you have a question or want to request a feature, please **DO NOT SUBMIT** a new issue.

Instead please use the relevant Discussions section's category:
- 🙏 [Ask a question](https://github.com/nginx-proxy/nginx-proxy/discussions/categories/q-a)
- 💡 [Request a feature](https://github.com/nginx-proxy/nginx-proxy/discussions/categories/ideas)

## Bugs

If you are logging a bug, please search the current open issues first to see if there is already a bug opened.

For bugs, the easier you make it to reproduce the issue you see and the more initial information you provide, the easier and faster the bug can be identified and can get fixed.

Please at least provide:
- the exact nginx-proxy version you're using (if using `latest` please make sure it is up to date and provide the version number printed at container startup).
- complete configuration (compose file, command line, etc) of both your nginx-proxy container(s) and proxied containers. You should redact sensitive info if needed but please provide **full** configurations.
- generated nginx configuration obtained with `docker exec nameofyournginxproxycontainer nginx -T`

If you can provide a script or docker-compose file that reproduces the problems, that is very helpful.

## General advice about `latest`

Do not use the `latest` tag for production setups.

`latest` is nothing more than a convenient default used by Docker if no specific tag is provided, there isn't any strict convention on what goes into this tag over different projects, and it does not carry any promise of stability.

Using `latest` will most certainly put you at risk of experiencing uncontrolled updates to non backward compatible versions (or versions with breaking changes) and makes it harder for maintainers to track which exact version of the container you are experiencing an issue with.

This recommendation stands for pretty much every Docker image in existence, not just nginx-proxy's ones. 

Thanks,
Nicolas
