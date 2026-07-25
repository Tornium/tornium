defmodule Tornium.Repo.Migrations.AddUserOnDelete do
  use Ecto.Migration

  def change do
    create_if_not_exists table("stat", primary_key: false) do
      add :id, :serial, primary_key: true
      add :tid_id, references(:user, column: :tid, type: :integer), null: false
      add :battlescore, :integer, null: false
      add :time_added, :naive_datetime, null: false
      add :added_group, :integer, null: false
    end

    create_if_not_exists index(:stat, [:battlescore], name: :stat_battlescore)
    create_if_not_exists index(:stat, [:tid_id, desc: :time_added], name: :stat_tid_id)
    create_if_not_exists index(:stat, [:added_group], name: :statnew_added_group)

    alter table(:stat) do
      modify :tid_id, references(:user, column: :tid, type: :integer, on_delete: :delete_all), from: references(:user, column: :tid, type: :integer), null: true
    end

    create_if_not_exists table("personalstats", primary_key: false) do
      add :user, references(:user, column: :tid, type: :integer), null: false, primary_key: true
      add :timestamp, :date, null: false, primary_key: true

      add :useractivity, :bigint, default: nil, null: true
      add :activestreak, :bigint, default: nil, null: true
      add :bestactivestreak, :bigint, default: nil, null: true
      add :itemsbought, :bigint, default: nil, null: true
      add :pointsbought, :bigint, default: nil, null: true
      add :itemsboughtabroad, :bigint, default: nil, null: true
      add :weaponsbought, :bigint, default: nil, null: true
      add :itemssent, :bigint, default: nil, null: true
      add :auctionswon, :bigint, default: nil, null: true
      add :auctionsells, :bigint, default: nil, null: true
      add :attackswon, :bigint, default: nil, null: true
      add :attackslost, :bigint, default: nil, null: true
      add :attacksdraw, :bigint, default: nil, null: true
      add :bestkillstreak, :bigint, default: nil, null: true
      add :moneymugged, :bigint, default: nil, null: true
      add :attacksstealthed, :bigint, default: nil, null: true
      add :attackhits, :bigint, default: nil, null: true
      add :attackmisses, :bigint, default: nil, null: true
      add :attackdamage, :bigint, default: nil, null: true
      add :attackcriticalhits, :bigint, default: nil, null: true
      add :respectforfaction, :bigint, default: nil, null: true
      add :onehitkills, :bigint, default: nil, null: true
      add :defendswon, :bigint, default: nil, null: true
      add :defendslost, :bigint, default: nil, null: true
      add :defendsstalemated, :bigint, default: nil, null: true
      add :bestdamage, :bigint, default: nil, null: true
      add :roundsfired, :bigint, default: nil, null: true
      add :yourunaway, :bigint, default: nil, null: true
      add :theyrunaway, :bigint, default: nil, null: true
      add :highestbeaten, :bigint, default: nil, null: true
      add :peoplebusted, :bigint, default: nil, null: true
      add :failedbusts, :bigint, default: nil, null: true
      add :peoplebought, :bigint, default: nil, null: true
      add :peopleboughtspent, :bigint, default: nil, null: true
      add :virusescoded, :bigint, default: nil, null: true
      add :cityfinds, :bigint, default: nil, null: true
      add :traveltimes, :bigint, default: nil, null: true
      add :bountiesplaced, :bigint, default: nil, null: true
      add :bountiesreceived, :bigint, default: nil, null: true
      add :bountiescollected, :bigint, default: nil, null: true
      add :totalbountyreward, :bigint, default: nil, null: true
      add :revives, :bigint, default: nil, null: true
      add :revivesreceived, :bigint, default: nil, null: true
      add :medicalitemsused, :bigint, default: nil, null: true
      add :statenhancersused, :bigint, default: nil, null: true
      add :trainsreceived, :bigint, default: nil, null: true
      add :totalbountyspent, :bigint, default: nil, null: true
      add :drugsused, :bigint, default: nil, null: true
      add :overdosed, :bigint, default: nil, null: true
      add :meritsbought, :bigint, default: nil, null: true
      add :personalsplaced, :bigint, default: nil, null: true
      add :classifiedadsplaced, :bigint, default: nil, null: true
      add :mailssent, :bigint, default: nil, null: true
      add :friendmailssent, :bigint, default: nil, null: true
      add :factionmailssent, :bigint, default: nil, null: true
      add :companymailssent, :bigint, default: nil, null: true
      add :spousemailssent, :bigint, default: nil, null: true
      add :largestmug, :bigint, default: nil, null: true
      add :cantaken, :bigint, default: nil, null: true
      add :exttaken, :bigint, default: nil, null: true
      add :kettaken, :bigint, default: nil, null: true
      add :lsdtaken, :bigint, default: nil, null: true
      add :opitaken, :bigint, default: nil, null: true
      add :shrtaken, :bigint, default: nil, null: true
      add :spetaken, :bigint, default: nil, null: true
      add :pcptaken, :bigint, default: nil, null: true
      add :xantaken, :bigint, default: nil, null: true
      add :victaken, :bigint, default: nil, null: true
      add :chahits, :bigint, default: nil, null: true
      add :heahits, :bigint, default: nil, null: true
      add :axehits, :bigint, default: nil, null: true
      add :grehits, :bigint, default: nil, null: true
      add :machits, :bigint, default: nil, null: true
      add :pishits, :bigint, default: nil, null: true
      add :rifhits, :bigint, default: nil, null: true
      add :shohits, :bigint, default: nil, null: true
      add :smghits, :bigint, default: nil, null: true
      add :piehits, :bigint, default: nil, null: true
      add :slahits, :bigint, default: nil, null: true
      add :argtravel, :bigint, default: nil, null: true
      add :mextravel, :bigint, default: nil, null: true
      add :dubtravel, :bigint, default: nil, null: true
      add :hawtravel, :bigint, default: nil, null: true
      add :japtravel, :bigint, default: nil, null: true
      add :lontravel, :bigint, default: nil, null: true
      add :soutravel, :bigint, default: nil, null: true
      add :switravel, :bigint, default: nil, null: true
      add :chitravel, :bigint, default: nil, null: true
      add :cantravel, :bigint, default: nil, null: true
      add :dumpfinds, :bigint, default: nil, null: true
      add :dumpsearches, :bigint, default: nil, null: true
      add :itemsdumped, :bigint, default: nil, null: true
      add :daysbeendonator, :bigint, default: nil, null: true
      add :caytravel, :bigint, default: nil, null: true
      add :jailed, :bigint, default: nil, null: true
      add :hospital, :bigint, default: nil, null: true
      add :attacksassisted, :bigint, default: nil, null: true
      add :bloodwithdrawn, :bigint, default: nil, null: true
      add :networth, :bigint, default: nil, null: true
      add :missionscompleted, :bigint, default: nil, null: true
      add :contractscompleted, :bigint, default: nil, null: true
      add :dukecontractscompleted, :bigint, default: nil, null: true
      add :missioncreditsearned, :bigint, default: nil, null: true
      add :consumablesused, :bigint, default: nil, null: true
      add :candyused, :bigint, default: nil, null: true
      add :alcoholused, :bigint, default: nil, null: true
      add :energydrinkused, :bigint, default: nil, null: true
      add :nerverefills, :bigint, default: nil, null: true
      add :unarmoredwon, :bigint, default: nil, null: true
      add :h2hhits, :bigint, default: nil, null: true
      add :organisedcrimes, :bigint, default: nil, null: true
      add :territorytime, :bigint, default: nil, null: true
      add :territoryjoins, :bigint, default: nil, null: true
      add :arrestsmade, :bigint, default: nil, null: true
      add :booksread, :bigint, default: nil, null: true
      add :traveltime, :bigint, default: nil, null: true
      add :boostersused, :bigint, default: nil, null: true
      add :rehabs, :bigint, default: nil, null: true
      add :rehabcost, :bigint, default: nil, null: true
      add :awards, :bigint, default: nil, null: true
      add :receivedbountyvalue, :bigint, default: nil, null: true
      add :racingskill, :bigint, default: nil, null: true
      add :raceswon, :bigint, default: nil, null: true
      add :racesentered, :bigint, default: nil, null: true
      add :racingpointsearned, :bigint, default: nil, null: true
      add :specialammoused, :bigint, default: nil, null: true
      add :cityitemsbought, :bigint, default: nil, null: true
      add :hollowammoused, :bigint, default: nil, null: true
      add :tracerammoused, :bigint, default: nil, null: true
      add :piercingammoused, :bigint, default: nil, null: true
      add :incendiaryammoused, :bigint, default: nil, null: true
      add :attackswonabroad, :bigint, default: nil, null: true
      add :defendslostabroad, :bigint, default: nil, null: true
      add :rankedwarringwins, :bigint, default: nil, null: true
      add :retals, :bigint, default: nil, null: true
      add :elo, :bigint, default: nil, null: true
      add :jobpointsused, :bigint, default: nil, null: true
      add :reviveskill, :bigint, default: nil, null: true
      add :itemslooted, :bigint, default: nil, null: true
      add :rankedwarhits, :bigint, default: nil, null: true
      add :raidhits, :bigint, default: nil, null: true
      add :territoryclears, :bigint, default: nil, null: true
      add :refills, :bigint, default: nil, null: true
    end

    alter table("personalstats") do
      modify(
        :user_id,
        references(:user, column: :tid, type: :integer, on_delete: :delete_all),
        from: references(:user, column: :tid, type: :integer), null: false
      )
    end

    alter table(:organized_crime_team_member) do
      modify(
        :user_id,
        references(:user, column: :tid, type: :integer, on_delete: :delete_all),
        from: references(:user, column: :tid, type: :integer), null: true
      )
    end

    alter table(:overdose_count) do
      modify(
        :user_id,
        references(:user, column: :tid, type: :integer, on_delete: :delete_all),
        from: references(:user, column: :tid, type: :integer), null: false
      )
    end

    alter table(:overdose_event) do
      modify(
        :user_id,
        references(:user, column: :tid, type: :integer, on_delete: :delete_all),
        from: references(:user, column: :tid, type: :integer), null: false
      )
    end
  end
end
