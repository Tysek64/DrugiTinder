// 5. Messages from the last 7 days with sender's name and surname (run on 'messages' collection)
[
  {
    $lookup:
      /**
       * from: The target collection.
       * localField: The local join field.
       * foreignField: The target join field.
       * as: The name for the results.
       * pipeline: Optional pipeline to run on the foreign collection.
       * let: Optional variables to use in the pipeline field stages.
       */
      {
        from: "users",
        localField: "sender_id",
        foreignField: "_id",
        as: "sender_data"
      }
  },
  {
    $match:
      /**
       * query: The query in MQL.
       */
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
      /**
       * specifications: The fields to
       *   include or exclude.
       */
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

// 7. Users with moxt expensive subscription plan (run on 'subscription_plans' collection)
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