# Arvee for Home Assistant

## Installation

To install you can use HACS, or manually copy into `custom_components`

Once installed, it will provide the `arvee.set_timezone` and `arvee.set_geo_timezone` service, which functions just like the `homeassistant.set_location` service allowing you to change the timezone via automation, etc. Note that Home Assistant’s UI makes some assumptions regarding timezones, e.g. `America/New_York` is what they call “Eastern Time”. So if you set it to something else that is also EST (e.g. `America/Detroit`) the 'Timezone" drop down in the settings page will be blank. I don’t know what, if any negative impact that will have on other things so YMMV.

This component will likely continue to expand in functionality specifically for RV / mobile installations of Home Assistant as necessary.

The library uses the Python `timezonefinder` package to look up timezones completely offline. It takes a pretty good amount of time to load the first time because it has to build the database.

### NOTE ON CONTAINER-BASED HOME ASSISTANT

The `timezonefinder` package requires the container to have compilers and build tools to install. You can read [here](https://github.com/home-assistant/core/issues/87682) as to why. To fix this you can log into the container with an interactive shell and install them manually:

```
$ docker exec -it homeassistant /bin/bash
$ apk add build-base
```

Then probably will want to do a `docker restart homeassistant` to trigger it to try to rebuild everything again which should work.

## Services

`arvee.set_timezone` - Provide a `timezone` key in `America/New_York` format to change the timezone of HASS dynamically
`arvee.set_geo_timezone` - Provide `latitude` and `longitude` keys to lookup the timezone based on that location and set it automatically.
