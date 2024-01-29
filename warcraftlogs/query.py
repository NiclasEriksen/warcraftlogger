
report_query = """
query($report_id:String){
    reportData{
        report(code:$report_id){
            code,
            title,
            startTime,
            endTime,
            segments,
            zone{
                name
            },
            rankedCharacters{
                classID,
                name
            },
            fights(killType: Kills){
                kill,
                name,
                startTime,
                endTime
            }
        }
    }
}"""

reports_query = """
query($guild_id:Int){
    reportData{
        reports(guildID:$guild_id, limit: 5){
            data{
                code,
                title,
                startTime,
                endTime,
                segments
                zone{
                    name
                },
            }
        }
    }
}"""

