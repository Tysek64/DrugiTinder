// 1. Active users' names, surnames, locations and subscription plans
[
  {
    $lookup: {
      from: "subscription_plans",
      localField: "subscription.plan_id",
      foreignField: "_id",
      as: "subscription_plan"
    }
  },
  {
    $project: {
      name: "$profile.name",
      surname: "$profile.surname",
      location: "$profile.location",
      subscription_plan: "$subscription_plan.name"
    }
  },
  {
    $sort:
      {
        surname: 1,
        name: 1
      }
  }
]

// 2. Number of users grouped by theri sex
[
  {
    $group:
      {
        _id: "$profile.sex",
        number_of_users: {
          $sum: 1
        }
      }
  }
]

// 3. Users with subscriptions expiring in the next 30 days
[
  {
    $match:
      {
        $expr: {
          $lte: [
            "$subscription.expiration_date",
            {
              $dateAdd: {
                startDate: "$$NOW",
                unit: "day",
                amount: 30
              }
            }
          ]
        }
      }
  },
  {
    $lookup:
      {
        from: "subscription_plans",
        localField: "subscription.plan_id",
        foreignField: "_id",
        as: "subscription_plan"
      }
  },
  {
    $project:
      {
        name: "$profile.name",
        surname: "$profile.surname",
        subscription_plan:
          "$subscription_plan.name",
        expiration_date:
          "$subscription.expiration_date"
      }
  }
]

// 4. Number of matches of users
[
  {
    $unwind:
      {
        path: "$members"
      }
  },
  {
    $group:
      {
        _id: "$members",
        match_count: {
          $sum: 1
        }
      }
  },
  {
    $lookup:
      {
        from: "users",
        localField: "_id",
        foreignField: "_id",
        as: "user"
      }
  },
  {
    $unwind:
      {
        path: "$user"
      }
  },
  {
    $project:
      {
        _id: "$user._id",
        name: "$user.profile.name",
        surname: "$user.profile.surname",
        match_count: "$match_count"
      }
  },
  {
    $sort:
      {
        match_count: -1
      }
  }
]

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

// 6. Number of messages in every conversation
[
  {
    $group:
      {
        _id: "$match_id",
        message_count: {
          $sum: 1
        }
      }
  },
  {
    $sort:
      {
        message_count: -1
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

// 8. Number of active blocks for every user
// Tego na razie sie nie da zrobic

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

// 12. Top 20 most active users in the last 30 days
[
  {
    $lookup: {
      from: "swipes",
      let: {
        user_id: "$_id"
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $gte: [
                "$swipe_time",
                {
                  $dateSubtract: {
                    startDate: "$$NOW",
                    unit: "day",
                    amount: 30
                  }
                }
              ]
            }
          }
        },
        {
          $group: {
            _id: "$swiper_id",
            swipe_count: {
              $sum: 1
            }
          }
        },
        {
          $match: {
            $expr: {
              $eq: ["$_id", "$$user_id"]
            }
          }
        }
      ],
      as: "swipes_count"
    }
  },
  {
    $unwind: {
      path: "$swipes_count"
    }
  },
  {
    $lookup: {
      from: "messages",
      let: {
        user_id: "$_id"
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $gte: [
                "$send_time",
                {
                  $dateSubtract: {
                    startDate: "$$NOW",
                    unit: "day",
                    amount: 30
                  }
                }
              ]
            }
          }
        },
        {
          $group: {
            _id: "$sender_id",
            message_count: {
              $sum: 1
            }
          }
        },
        {
          $match: {
            $expr: {
              $eq: ["$_id", "$$user_id"]
            }
          }
        }
      ],
      as: "messages_count"
    }
  },
  {
    $unwind: {
      path: "$messages_count",
      preserveNullAndEmptyArrays: true
    }
  },
  {
    $project: {
      name: "$profile.name",
      surname: "$profile.surname",
      swipes_count: "$swipes_count.swipe_count",
      messages_count: {
        $ifNull: [
          "$messages_count.message_count",
          0
        ]
      },
      total_activity: {
        $add: [
          "$swipes_count.swipe_count",
          {
            $ifNull: [
              "$messages_count.message_count",
              0
            ]
          }
        ]
      }
    }
  },
  {
    $sort: {
      total_activity: -1
    }
  },
  {
    $limit: 20
  }
]
// Za dlugo sie wykonuje, trzeba bedzie cos zmienic

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

// 14. Matches ended in the last 30 days
[
  {
    $match: {
      $expr: {
        $gte: [
          "$date_ended",
          {
            $dateSubtract: {
              startDate: "$$NOW",
              unit: "day",
              amount: 30
            }
          }
        ]
      }
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "members.0",
      foreignField: "_id",
      as: "user_1"
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "members.1",
      foreignField: "_id",
      as: "user_2"
    }
  },
  {
    $unwind: {
      path: "$user_1"
    }
  },
  {
    $unwind: {
      path: "$user_2"
    }
  },
  {
    $project: {
      user1: {
        $concat: [
          "$user_1.profile.name",
          " ",
          "$user_1.profile.surname"
        ]
      },
      user2: {
        $concat: [
          "$user_2.profile.name",
          " ",
          "$user_2.profile.surname"
        ]
      },
      date_formed: 1,
      date_ended: 1
    }
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

// 18. Average match time in days grouped by month
[
  {
    $group: {
      _id: {
        $month: "$date_formed"
      },
      avg_duration_days: {
        $avg: {
          $dateDiff: {
            startDate: "$date_formed",
            endDate: {
              $ifNull: ["$date_ended", "$$NOW"]
            },
            unit: "day"
        	}
        }
      },
      match_count: {
        $sum: 1
      }
    }
  }
]

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

// 20. 

