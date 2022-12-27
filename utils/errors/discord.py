# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>


class DiscordError(Exception):
    def __init__(self, code, message):
        super().__init__()

        self.code = code
        self.message = message

    def __str__(self):
        return f"The Discord API has return error code {self.code}"

    def __reduce__(self):
        return self.__class__, (self.code, self.message)