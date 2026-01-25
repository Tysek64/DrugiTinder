// 5. Messages from the last 7 days with sender's name and surname (run on 'messages' collection)
[
  {
    $lookup:
      {
        from: "users",
        localField: "sender_id",
        foreignField: "_id",
        as: "sender_data"
      }
  },
  {
    $match:
      {
        $expr: {
          $gte: [
            "$send_time",
            {
              $dateSubtract: {
                startDate: "$$NOW",
                unit: "day",
                amount: 7
              }
            }
          ]
        }
      }
  },
  {
    $project:
      {
        _id: 1,
        name: {
          $first: "$sender_data.profile.name"
        },
        surname: {
          $first: "$sender_data.profile.surname"
        },
        contents: 1,
        send_time: 1
      }
  }
]

// 7. Users with most expensive subscription plan (run on 'subscription_plans' collection)
[
  {
    $sort: {
      price_per_month: -1
    }
  },
  {
    $limit: 1
  },
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "subscription.plan_id",
      as: "users_with_most_expensive_plan"
    }
  },
  {
    $unwind: "$users_with_most_expensive_plan"
  },
  {
    $project: {
      _id: "$users_with_most_expensive_plan._id",
      username:
        "$users_with_most_expensive_plan.username",
      plan_name: "$name",
      price: "$price_per_month"
    }
  }
]

// 9. Banned users with reason and date (run on 'users' collection)
[
  {
    $match: {
      "is_banned": true
    }
  },

  {
    $project: {
      _id: 1,
      username: 1,
      reason: "$ban_details.reason",
      expires: "$ban_details.expires_at"
    }
  }
]

//10. Average hobby interest among users (run on 'users' collection)
[
  {
   	$unwind: "$profile.interests"
  },

  {
   	$addFields: {
      "profile.interests.adjusted_level": {
        $cond: { 
          if: { $eq: ["$profile.interests.is_positive", true] }, 
          then: "$profile.interests.level", 
          else: {$multiply: ["$profile.interests.level", -1]}}
        }
    } 
  },
  
  {
    $group: {
      _id: "$profile.interests.name",
      average_level: { $avg: "$profile.interests.adjusted_level" },
      user_count: { $sum: 1 }
    }
  },

  {
    $project: {
      hobby: "$_id",
      average_interest: "$average_level",
      user_count: "$user_count",
      _id: 0
    }
  }
]

// 11. Users with auto renewing subscriptions (run on 'users' collection)
[
  {
    $match: {
      "subscription.auto_renewal": true
    }
  }
]
// or just the ' "subscription.auto_renewal": true ' query in a simple find()

// 13. Most popular hobbies in matches (run on 'matches' collection)
[
  {
    $lookup:
      {
        from: "users",
        localField: "members",
        foreignField: "_id",
        as: "parties"
      }
  },

  { $unwind: "$parties"},

  { $unwind: "$parties.profile.interests" },

  {
    $group: {
      _id: {
        match_id: "$_id",
        interest_name: "$parties.profile.interests.name"
      }
    }
  },

  {
    $group: {
      _id: "$_id.interest_name",
      matches: { $sum: 1 }
    }
  },

  {
    $sort: { matches: -1}
  }
]

// 15. Users without profile images (run on 'users' collection) (not an aggregation, run as a simple query)
{
    $or: [
      {"profile.images": { $exists: false}},
      {"profile.images": {$eq: null}},
      {"profile.images": { $size: 0 } }
    ]
  }

// 16. Average reaction time in conversations (run on 'messages' collection)
// Add this index if you want to survive this query:
db.messages.createIndex({ "send_time": 1, "match_id": 1 })

// Time frame is specified so as to complete the query in reasonable time
[
  {
    $match: {
      send_time: {
        $gte: ISODate("2026-01-01T00:00:00Z"),
        $lt: ISODate("2026-02-07T00:00:00Z")
      }
    }
  },
  {
    $setWindowFields: {
      partitionBy: "$match_id",
      sortBy: {
        send_time: 1
      },
      output: {
        prev_sender: {
          $shift: {
            output: "$sender_id",
            by: -1
          }
        },
        prev_send_time: {
          $shift: {
            output: "$send_time",
            by: -1
          }
        }
      }
    }
  },
  {
    $match: {
      $expr: {
        $and: [
          {
            $ne: ["$prev_sender", null]
          },
          {
            $ne: ["$sender_id", "$prev_sender"]
          }
        ]
      }
    }
  },
  {
    $addFields: {
      diff_min: {
        $dateDiff: {
          startDate: "$prev_send_time",
          endDate: "$send_time",
          unit: "minute"
        }
      }
    }
  },
  {
    $group: {
      _id: "$match_id",
      avg_response_time_min: {
        $avg: "$diff_min"
      },
      total_responses: {
        $sum: 1
      }
    }
  },
  {
    $project: {
      match_id: "$_id",
      avg_response_time_min: 1,
      total_responses: 1,
      _id: 1
    }
  },
  {
    $merge: {
      into: "report_avg_response_times", 
      on: "_id",                         
      whenMatched: "replace",            
      whenNotMatched: "insert"           
    }
  }
]

// 17. Users who were never blocked (run on 'users' collection)
// Requires blocks_history collection, which is not currently generated by the populating scripts. maybe add it later.
[
  {
    $lookup:
      {
        from: "blocks_history",
        localField: "_id",
        foreignField: "blocked_id",
        as: "block_records"
      }
  },
  {
    $match:
      {
        block_records: {
          $size: 0
        }
      }
  },
  {
    $project:
      {
        username: 1
      }
  }
]

// lub w mongo shell:
db.blocks_history.distinct("blocked_id")
// skopiuj wszystkie id i wklej do mongo shell
db.users.find({
  "_id": { $nin: [/*wklej tutaj skopiowane id*/] }
}).project({ username: 1 });

// 19. Users with active subscription without any matches (run on 'users' collection)
[
  {
    $match: {
      "subscription.is_active": true
    }
  },
  {
    $lookup: {
      from: "matches",
      localField: "_id",
      foreignField: "members", 
      pipeline: [
        { $limit: 1 }, 
        { $project: { _id: 1 } }
      ],
      as: "user_matches"
    }
  },
  {
    $match: {
      "user_matches": { $size: 0 }
    }
  },
  {
    $project: {
      username: 1,
      _id: 1
    }
  }
]