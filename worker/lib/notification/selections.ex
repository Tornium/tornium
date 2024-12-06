defmodule Tornium.Notification.Selections do
  # NOTE: Use 
  # :%s/\v: \([^,]*, / =>
  # to replace the necessary text from the python version of this

  # For ease of development, this does not have a map of lists
  @api_selections %{
                    user: %{
                      "ammo" => "ammo",
                      "attacks" => "attacks",
                      "chain" => "bars",
                      "energy" => "bars",
                      "happy" => "bars",
                      "nerve" => "bars",
                      "gender" => "basic",
                      "level" => "basic",
                      "name" => "basic",
                      "player_id" => "basic",
                      "status" => "basic",
                      "defense" => "battlestats",
                      "defense_info" => "battlestats",
                      "defense_modifier" => "battlestats",
                      "dexterity" => "battlestats",
                      "dexterity_info" => "battlestats",
                      "dexterity_modifier" => "battlestats",
                      "speed" => "battlestats",
                      "speed_info" => "battlestats",
                      "speed_modifier" => "battlestats",
                      "strength" => "battlestats",
                      "strength_info" => "battlestats",
                      "strength_modifier" => "battlestats",
                      "total" => "battlestats",
                      "bazaar" => "bazaar",
                      "cooldowns" => "cooldowns",
                      "criminalrecord" => "criminalrecord",
                      "discord" => "discord",
                      "display" => "display",
                      "education_completed" => "education",
                      "education_current" => "education",
                      "education_timeleft" => "education",
                      "equipment" => "equipment",
                      "events" => "events",
                      "activegym" => "gym",
                      "halloffame" => "hof",
                      "honors_awarded" => "honors",
                      "honors_time" => "honors",
                      "icons" => "icons",
                      "jobpoints" => "jobpoints",
                      "selections" => "lookup",
                      "medals_awarded" => "medals",
                      "medals_time" => "medals",
                      "merits" => "merits",
                      "messages" => "messages",
                      "missions" => "missions",
                      "cayman_bank" => "money",
                      "city_bank" => "money",
                      "company_funds" => "money",
                      "daily_networth" => "money",
                      "money_onhand" => "money",
                      "points" => "money",
                      "vault_amount" => "money",
                      "networth" => "networth",
                      "notifications" => "notifications",
                      "book_perks" => "perks",
                      "education_perks" => "perks",
                      "enhancer_perks" => "perks",
                      "faction_perks" => "perks",
                      "job_perks" => "perks",
                      "merit_perks" => "perks",
                      "property_perks" => "perks",
                      "stock_perks" => "perks",
                      "personalstats" => "personalstats",
                      "age" => "profile",
                      "awards" => "profile",
                      "basicicons" => "profile",
                      "competition" => "profile",
                      "donator" => "profile",
                      "enemies" => "profile",
                      "faction" => "profile",
                      "forum_posts" => "profile",
                      "friends" => "profile",
                      "honor" => "profile",
                      "job" => "profile",
                      "karma" => "profile",
                      "last_action" => "profile",
                      "life" => "profile",
                      "married" => "profile",
                      "profile_image" => "profile",
                      "property" => "profile",
                      "property_id" => "profile",
                      "rank" => "profile",
                      "signup" => "profile",
                      "states" => "profile",
                      "properties" => "properties",
                      "baned" => "publicstatus",
                      "playername" => "publicstatus",
                      "userID" => "publicstatus",
                      "refills" => "refills",
                      "reports" => "reports",
                      "revives" => "revives",
                      "bootlegging" => "skills",
                      "burglary" => "skills",
                      "card_skimming" => "skills",
                      "cracking" => "skills",
                      "disposal" => "skills",
                      "forgery" => "skills",
                      "graffiti" => "skills",
                      "hunting" => "skills",
                      "hustling" => "skills",
                      "pickpocketing" => "skills",
                      "racing" => "skills",
                      "reviving" => "skills",
                      "search_for_cash" => "skills",
                      "shoplifting" => "skills",
                      "stocks" => "stocks",
                      "timestamp" => "timestamp",
                      "travel" => "travel",
                      "weaponxp" => "weaponxp",
                      "workstats" => "workstats"
                    },
                    faction: %{
                      "applications" => "applications",
                      "armor" => "armor",
                      "armorynews" => "armorynews",
                      "attacknews" => "attacknews",
                      "attacks" => "attacks",
                      "age" => "basic",
                      "best_chain" => "basic",
                      "capacity" => "basic",
                      "co-leader" => "basic",
                      "ID" => "basic",
                      "leader" => "basic",
                      "members" => "basic",
                      "name" => "basic",
                      "peace" => "basic",
                      "raid_wars" => "basic",
                      "rank" => "basic",
                      "ranked_wars" => "basic",
                      "respect" => "basic",
                      "tag" => "basic",
                      "tag_image" => "basic",
                      "territory_wars" => "basic",
                      "boosters" => "boosters",
                      "caches" => "caches",
                      "cesium" => "cesium",
                      "chain" => "chain",
                      "chain_report" => "chain_report",
                      "chains" => "chains",
                      "crimeexp" => "crimeexp",
                      "crimenews" => "crimenews",
                      "crimes" => "crimes",
                      "money" => "currency",
                      "points" => "currency",
                      "donations" => "donations",
                      "drugs" => "drugs",
                      "fundsnews" => "fundsnews",
                      "mainnews" => "mainnews",
                      "medical" => "medical",
                      "membershipnews" => "membershipnews",
                      "positions" => "positions",
                      "rankedwars" => "rankedwars",
                      "reports" => "reports",
                      "revives" => "revives",
                      "stats" => "stats",
                      "temporary" => "temporary",
                      "territory" => "territory",
                      "territorynews" => "territorynews",
                      "upgrades" => "upgrades",
                      "weapons" => "weapons"
                    }
                  }
                  |> Enum.map(fn {key, selections} ->
                    {key, Enum.group_by(selections, fn {_k, v} -> v end, fn {k, _v} -> k end)}
                  end)

  @spec get_selection_keys(resource :: Tornium.Notification.trigger_resource(), selection :: String.t()) :: [String.t()]
  def get_selection_keys(resource, selection) do
    @api_selections[resource][selection] || []
  end
end
