# Copyright (C) 2021-2025 tiksan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

defmodule Tornium.Test.Faction.News.ArmoryAction do
  use Tornium.RepoCase, async: true
  alias Tornium.Faction.News.ArmoryAction
  alias Torngen.Client.Schema.FactionNews

  test "use item ending in 'x '" do
    news = %FactionNews{
      id: "55RrWavfGpBGng5mCYUk",
      text:
        "<a href = \"http://www.torn.com/profiles.php?XID=1\">Chedburn</a> gave 2992x Box of Extra Strong Mints to themselves from the faction armory",
      timestamp: 1_764_118_665
    }

    assert %ArmoryAction{
             id: "55RrWavfGpBGng5mCYUk",
             action: :give,
             user_id: 1,
             recipient_id: 1,
             item_id: 39,
             quantity: 2992
           } = ArmoryAction.parse(news)
  end

  test "fill bloodbag" do
    news = %FactionNews{
      id: "1Et5m6YNr2iDZErRHo1a",
      text:
        "<a href = \"http://www.torn.com/profiles.php?XID=1\">Chedburn</a> filled one of the faction's Empty Blood Bag items",
      timestamp: 1_764_177_585
    }

    assert %ArmoryAction{
             id: "1Et5m6YNr2iDZErRHo1a",
             action: :fill,
             user_id: 1,
             recipient_id: 1,
             item_id: 731,
             quantity: 1
           } = ArmoryAction.parse(news)
  end

  test "use beer" do
    news = %FactionNews{
      id: "jDECKiHFkj9EKh7iLWG0",
      text:
        "<a href = \"http://www.torn.com/profiles.php?XID=1\">Chedburn</a> used one of the faction's Bottle of Beer items",
      timestamp: 1_764_167_520
    }

    assert %ArmoryAction{
      id: "jDECKiHFkj9EKh7iLWG0",
      action: :use,
      user_id: 1,
      recipient_id: 1,
      item_id: 180,
      quantity: 1,
    } = ArmoryAction.parse(news)
  end
end
