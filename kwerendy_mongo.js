// 5. Messages from the last 7 days with sender's name and surname
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