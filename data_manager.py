from psycopg2 import sql
import connection
import datetime


# gets data from sql TABLE
@connection.connection_handler
def get_data(cursor, table_name):
    cursor.execute(sql.SQL("""SELECT * FROM {table};
                    """).format(table=sql.Identifier(table_name)))
    data = cursor.fetchall()
    return data


@connection.connection_handler
def display_latest_five_questions(cursor):
    cursor.execute("""
                    SELECT title FROM question
                    ORDER BY submission_time DESC 
                    LIMIT 5;
                    """)
    questions = cursor.fetchall()
    return questions


@connection.connection_handler
def search_question_pattern(cursor, pattern):
    cursor.execute("""
                        SELECT title FROM question
                        WHERE LOWER(title) LIKE LOWER(%(pattern)s)
                        UNION 
                        SELECT message FROM answer
                        WHERE LOWER(message) LIKE LOWER(%(pattern)s);
                        """,
                   {'pattern': '%' + pattern + '%'})
    search_results = cursor.fetchall()
    highlighted_list = []
    for dictionary in search_results:
        temp = dictionary['title'].lower().replace(pattern, f'<mark class = "highlight">{pattern}</mark>')
        highlighted_list.append(temp)
    return highlighted_list


@connection.connection_handler
def add_questions(cursor, title, message, user_id , image=None):
    submission_time = datetime.datetime.utcnow().isoformat(' ', 'seconds')
    cursor.execute(""" INSERT INTO question (submission_time, view_number, vote_number,title,message,user_id,image)
                        VALUES ( %(submission_time)s, 0, 0, %(title)s, %(message)s, %(user_id)s, %(image)s);
    """, {'submission_time': submission_time,
         'title': title,
         'message': message,
         'user_id':user_id,
         'image': image,})


@connection.connection_handler
def update_question(cursor, question_id, title, message ):
    
    cursor.execute(""" UPDATE question
                       SET title = %(title)s, message = %(message)s
                       WHERE id = %(question_id)s;
    """,
                   {'title': title,
                    'message': message,
                    'question_id': question_id})

@connection.connection_handler
def get_count_number(cursor,question_id):
    cursor.execute(""" SELECT view_number
                       FROM question 
                       WHERE id = %(question_id)s;""",
                       {'question_id': question_id})
    count = cursor.fetchone()
    return count

@connection.connection_handler
def update_view_count(cursor,count, question_id):
    cursor.execute("""UPDATE question
                     SET view_number = %(count)s + 1
                     WHERE id = %(question_id)s;
    """, {'count': count, 'question_id': question_id})

@connection.connection_handler
def delete_from_table(cursor,question_id):
    answers = get_data('answer')
    print(answers)
    answer_ids = []
    for answer in answers:
        if answer['question_id'] == int(question_id):
            answer_ids.append(answer['id'])
    print (answer_ids)
    for answer_id in answer_ids:
        cursor.execute(""" DELETE FROM comment
                            WHERE answer_id = %(answer_id)s
                            """, {'answer_id': answer_id})

    cursor.execute(""" DELETE FROM comment 
                          WHERE  question_id = %(question_id)s;                   
            """, {'question_id': question_id})

    cursor.execute(""" DELETE FROM answer
                           WHERE  question_id = %(question_id)s;                      
            """, {'question_id': question_id})

    cursor.execute(""" DELETE FROM question_tag
                           WHERE  question_id = %(question_id)s;                      
        """, {'question_id': question_id})

    cursor.execute(""" DELETE FROM question
                       WHERE  id = %(question_id)s;                      
    """, {'question_id': question_id})


@connection.connection_handler
def delete_answer(cursor, answer_id):
    cursor.execute("""
                        DELETE FROM comment
                        WHERE answer_id = %(answer_id)s;
        """, {'answer_id': answer_id})
    cursor.execute("""
                    DELETE FROM answer
                    WHERE id = %(answer_id)s;
    """,{'answer_id': answer_id})


@connection.connection_handler
def get_answer(cursor, answer_id):
    cursor.execute(""" SELECT *
                       FROM answer 
                        WHERE id = %(answer_id)s;
            """, {'answer_id': answer_id})
    details = cursor.fetchall()
    return details

@connection.connection_handler
def get_answers_for_question(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM answer WHERE question_id = %(question_id)s ORDER BY vote_number DESC;
    """,
                   {'question_id': question_id})
    answers = cursor.fetchall()
    return answers

@connection.connection_handler
def update_answer(cursor,answer_id,message):
    cursor.execute(""" UPDATE answer
                           SET  message = %(message)s
                           WHERE id = %(answer_id)s
        """,
                   {'message': message,
                    'answer_id': answer_id})

@connection.connection_handler
def post_answer(cursor, question_id, message, user_id, image=None):
    submission_time = datetime.datetime.utcnow().isoformat(' ', 'seconds')
    cursor.execute("""
                    INSERT INTO answer (submission_time, vote_number, question_id, message, user_id, image)
                    VALUES (%(submission_time)s, 0, %(question_id)s, %(message)s,%(user_id)s, %(image)s)
    """,{'submission_time' : submission_time,
         'question_id': question_id,
         'message' : message,
         'user_id': user_id,
         'image': image})

@connection.connection_handler
def get_question_id(cursor, answer_id):
    cursor.execute(""" SELECT * FROM answer
                        WHERE id = %(answer_id)s
    """,{'answer_id': answer_id})
    info_dict = cursor.fetchone()
    question_id = info_dict['question_id']
    return question_id

@connection.connection_handler
def vote_up_question(cursor, question_id):
    cursor.execute(""" UPDATE question
                       SET vote_number = vote_number + 1
                       WHERE id = %(question_id)s;
    """,
                   {'question_id': question_id})

@connection.connection_handler
def vote_down_question(cursor, question_id):
    cursor.execute(""" UPDATE question
                       SET vote_number = vote_number - 1
                       WHERE id = %(question_id)s;
    """,
                   {'question_id': question_id})


@connection.connection_handler
def get_tags(cursor, question_id):
    cursor.execute("""
    SELECT tag.id,tag.name FROM tag
     INNER JOIN question_tag ON tag.id = question_tag.tag_id
     WHERE question_tag.question_id = %(question_id)s
    """,
                   {'question_id': question_id})
    tags = cursor.fetchall()
    distinct_tags = list(set([tag['name'] for tag in tags]))
    return distinct_tags


@connection.connection_handler
def add_new_tag(cursor, tag):
    cursor.execute("""
    INSERT INTO tag (name) VALUES ( %(tag)s);""",
                   {'tag': tag})


@connection.connection_handler
def add_new_tag_id(cursor,question_id):
    cursor.execute("""
    SELECT id FROM tag 
    ORDER BY id DESC
    LIMIT 1 """)
    info_tag = cursor.fetchone()
    tag_ids = info_tag['id']
    cursor.execute("""
    INSERT INTO question_tag (question_id, tag_id) VALUES (%(question_id)s, %(tag_id)s) ;""",
                   {'question_id': question_id,
                    'tag_id': tag_ids})

    
    
@connection.connection_handler
def vote_up_answer(cursor, answer_id):
    cursor.execute(""" UPDATE answer
                       SET vote_number = vote_number + 1
                       WHERE id = %(answer_id)s;
    """,
                   {'answer_id': answer_id})

@connection.connection_handler
def vote_down_answer(cursor, answer_id):
    cursor.execute(""" UPDATE answer
                       SET vote_number = vote_number -1
                       WHERE id = %(answer_id)s;
    """,
                   {'answer_id': answer_id})


@connection.connection_handler
def get_comments(cursor, question_id, answer_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE question_id = %s;
                   """,
                   (question_id,)
                   )
    cursor.execute("""
                        SELECT * FROM comment
                        WHERE answer_id = %s;
                       """,
                   (answer_id,)
                   )
    comments = cursor.fetchall()
    return comments

@connection.connection_handler
def get_answer_data_by_answer_id(cursor, answer_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE id = %s;
                   """,
                   (answer_id,)
                   )
    answer_data = cursor.fetchall()
    return answer_data

@connection.connection_handler
def get_question_id_from_answer_id(cursor, answer_id):
    cursor.execute("""
                    SELECT question.id
                    FROM question
                    INNER JOIN answer
                    ON (question.id=answer.question_id)
                    WHERE answer.id=%s;
                    """,
                   (answer_id,))
    return cursor.fetchall()


@connection.connection_handler
def add_new_question_comment(cursor, question_comment):
    cursor.execute("""
                    INSERT INTO comment (id, question_id, message, submission_time, edited_count,user_id)
                    VALUES (%s, %s, %s, %s, %s,%s)
                    """,
                   (question_comment['id'],
                    question_comment['question_id'],
                    question_comment['message'],
                    question_comment['submission_time'],
                    question_comment['edited_count'],
                    question_comment['user_id'],   )
                    )


@connection.connection_handler
def add_new_answer_comment(cursor, answer_comment):
    cursor.execute("""
                    INSERT INTO comment (id, answer_id, message, submission_time, edited_count, user_id)
                    VALUES (%s, %s, %s, %s, %s,%s)
                    """,
                   (answer_comment['id'],
                    answer_comment['answer_id'],
                    answer_comment['message'],
                    answer_comment['submission_time'],
                    answer_comment['edited_count'],
                    answer_comment['user_id'],)
                    )


@connection.connection_handler
def get_comments_for_question(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE question_id = %s ORDER BY submission_time ASC;
                   """,
                   (question_id,)
                   )
    question_comments = cursor.fetchall()
    return question_comments


@connection.connection_handler
def get_comments_for_answers(cursor, question_id, answer_id_list):
    if not answer_id_list:
        answer_id_list.append('0')
    answer_id_str = ', '.join(answer_id_list)

    cursor.execute(f"""
                    SELECT * FROM comment
                    WHERE answer_id = {question_id} or  answer_id IN ({answer_id_str})
                    ORDER BY submission_time ASC;
                   """)
    answers_comments = cursor.fetchall()
    return answers_comments


@connection.connection_handler
def delete_comment(cursor, comment_id):

    cursor.execute("""
                    DELETE FROM comment
                    WHERE id = %s;
                   """,
                   (comment_id,))


@connection.connection_handler
def get_q_and_a_id_from_comment(cursor, comment_id):
    cursor.execute("""
                    SELECT question_id,answer_id FROM comment
                    WHERE id = %s;
                   """,
                   (comment_id,)
                   )
    question_id = cursor.fetchall()
    return question_id


@connection.connection_handler
def get_comment(cursor, comment_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE id = %s;
                   """,
                   (comment_id,)
                   )
    comment = cursor.fetchall()
    return comment


@connection.connection_handler
def edit_comment(cursor, comment):
    cursor.execute("""
                    UPDATE comment
                    SET message = %s, edited_count = %s
                    WHERE id = %s;
                   """,
                   (comment['message'],
                    comment['edited_count'],
                    comment['id'],)
                   )
@connection.connection_handler
def add_user(cursor, user_name, first_name, last_name, email, password):
    cursor.execute(""" INSERT INTO users ( user_name,first_name, last_name, email, password )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                   (user_name,first_name,last_name,email,password))


@connection.connection_handler
def get_user(cursor, user_name):
    cursor.execute(""" SELECT * FROM users
                      WHERE user_name = %s;
    """, (user_name,))
    details = cursor.fetchone()
    return details

@connection.connection_handler
def get_all_users(cursor):
    cursor.execute(""" SELECT * FROM users """)
    details = cursor.fetchall()
    return details


@connection.connection_handler
def get_user_after_id(cursor, id):
    cursor.execute(""" SELECT * FROM users
                      WHERE id = %s;
    """, (id,))
    details = cursor.fetchall()
    return details


@connection.connection_handler
def existing_user(cursor, user_name, email):
    cursor.execute(""" SELECT * FROM users
                      WHERE user_name = %s OR 
                      email = %s;
    """, (user_name, email))
    details = cursor.fetchall()
    return details

@connection.connection_handler
def get_user_id_from_username(cursor,username):
    cursor.execute(""" SELECT id 
                       FROM users
                       WHERE user_name = %s;
    """, (username,))
    user_id = cursor.fetchone()
    return user_id


@connection.connection_handler
def get_questions_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT id, title, message, image FROM question
                    WHERE user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    questions_dict_list = cursor.fetchall()
    return questions_dict_list


@connection.connection_handler
def get_answers_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT answer.message, answer.image, answer.question_id, answer.accepted, answer.id, question.title
                    FROM answer 
                    JOIN question ON answer.question_id = question.id
                    WHERE answer.user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    answers_dict_list = cursor.fetchall()
    return answers_dict_list


@connection.connection_handler
def get_comments_by_user_id(cursor, user_id):
    cursor.execute("""
                    SELECT answer.message AS ans_mes, question.id, question.title, comment.message
                    FROM answer 
                    JOIN question ON answer.question_id = question.id
                    JOIN comment ON answer.id = comment.answer_id
                    WHERE comment.user_id = %(user_id)s
                    UNION
                    SELECT null, question.id, question.title, comment.message
                    FROM question 
                    JOIN comment ON question.id = comment.question_id
                    WHERE comment.user_id = %(user_id)s;
                    """,
                   {'user_id': user_id})
    comments_dict_list = cursor.fetchall()
    return comments_dict_list

@connection.connection_handler
def get_user_for_question(cursor, question_id):
    cursor.execute("""SELECT user_name FROM users 
                    JOIN question ON question.user_id = users.id
                        WHERE question.id = %(question_id)s ;
                        """, {'question_id': question_id})
    data = cursor.fetchone()
    return data

@connection.connection_handler
def user_for_answer(cursor, user_ids):
    if not user_ids:
        user_ids.append('0')
    user_id_str = ', '.join(user_ids)
    cursor.execute(f""" SELECT DISTINCT user_name, users.id
                        FROM users
                        JOIN answer ON answer.user_id = users.id
                        WHERE users.id IN ({user_id_str})
                        """)
    users = cursor.fetchall()
    return users



@connection.connection_handler
def mark_answer_as_accepted(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer 
                    SET accepted = TRUE 
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})


@connection.connection_handler
def unmark_accepted_answer(cursor, answer_id):
    cursor.execute("""
                    UPDATE answer 
                    SET accepted = FALSE 
                    WHERE id = %(answer_id)s;
                    """,
                   {'answer_id': answer_id})

@connection.connection_handler
def select_reputation(cursor, user_id):
    cursor.execute("""
                    SELECT reputation
                    FROM users
                    WHERE id=%(user_id)s;
                    """,
                   {'user_id': user_id}
                   )
    reputation = cursor.fetchone()
    return reputation


@connection.connection_handler
def edit_reputation(cursor, vote, vote_type, user_name):
    reputation = 0
    if vote == -1:
        reputation = - 2
    elif vote == 1:
        if vote_type == 'question':
            reputation = 5
        elif vote_type == 'answer':
            reputation = 10

    cursor.execute("""
                    UPDATE users
                    SET reputation =
                    (SELECT reputation  
                    FROM users 
                    WHERE user_name = %(user_name)s)+%(reputation)s
                    WHERE user_name = %(user_name)s;

                    """, {'user_name': user_name, 'reputation': reputation})

@connection.connection_handler
def get_answer_owner(cursor, answer_id):
    cursor.execute(""" 
                    SELECT user_id
                    FROM answer
                    WHERE id = %(answer_id)s
                    """, {'answer_id': answer_id})
    user_i = cursor.fetchone()['user_id']
    return user_i

@connection.connection_handler
def get_question_owner(cursor, question_id):
    cursor.execute(""" 
                    SELECT user_id
                    FROM question
                    WHERE id = %(question_id)s
                    """, {'question_id': question_id})

    user_i = cursor.fetchone()['user_id']
    return user_i


@connection.connection_handler
def get_user_name_after_id(cursor, id):
    cursor.execute(""" SELECT user_name 
                       FROM users
                       WHERE id = %(id)s;
    """, {'id': id})
    user = cursor.fetchone()['user_name']
    return user