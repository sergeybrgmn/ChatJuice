create table users(
    id integer primary key,
    external_user_id int,
    username text,
    phone text,
    login_hash text,
    is_logged_in int,
    created datetime
);

create table users_balance(
    id integer primary key,
    user_id int,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

create table requests(
    id integer primary key,
    request_type int,
    user_id int,
    token_length int,
    created datetime,
    FOREIGN KEY (user_id) REFERENCES users(id)
);