# Arvee for Home Assistant

## Installation

To install you can use HACS, or manually copy into `custom_components`

Once installed, it will provide the `arvee.set_timezone` service, which functions just like the `homeassistant.set_location` service allowing you to change the timezone via automation, etc. Note that Home Assistant’s UI makes some assumptions regarding timezones, e.g. `America/New_York` is what they call “Eastern Time”. So if you set it to something else that is also EST (e.g. `America/Detroit`) the 'Timezone" drop down in the settings page will be blank. I don’t know what, if any negative impact that will have on other things so YMMV.

This component will likely continue to expand in functionality specifically for RV / mobile installations of Home Assistant as necessary.
