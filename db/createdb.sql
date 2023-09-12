create table budget(
    codename varchar(255) primary key,
    daily_limit integer
);

create table category(
    codename varchar(255) primary key,
    name varchar(255),
    is_base_expense boolean,
    aliases text
);

create table expense(
    id integer primary key,
    amount integer,
    created datetime,
    category_codename integer,
    raw_text text,
    FOREIGN KEY(category_codename) REFERENCES category(codename)
);

insert into category (codename, name, is_base_expense, aliases)
values
    ("products", "продукты", true, "еда"),
    ("coffee", "кофе", true, ""),
    ("dinner", "обед", true, "столовая, ланч, бизнес-ланч, бизнес ланч"),
    ("transport", "общ. транспорт", true, "метро, автобус, metro"),
    ("phone", "телефон", true, "yota, связь"),
    ("internet", "интернет", true, "инет, inet"),
    ("subscriptions", "подписки", true, "подписка"),
    ("housewares", "хоз. товары", true, "уборка, мытье, стирка"),
    ("cosmetics", "косметика", true, "уход, гигиена, ногти, лазер"),
    ("pharmacy", "аптека", true, "лекарства , витамины"),
    ("apartment", "квартира", true, "коммуналка, аренда"),
    ("entertainment", "развлечения", false, "боулинг, кино, отдых, музей, экскурсия, аквапарк, зоопарк, москвариум"),
    ("cafe", "кафе", false, "ресторан, рест, мак, макдональдс, макдак, kfc"),
    ("taxi", "такси", false, "яндекс такси, yandex taxi"),
    ("books", "книги", false, "литература, литра, лит-ра"),
    ("games", "игры", false, "стим, настолки"),
    ("outfit", "одежда", false, "наряд, платье, костюм, обувь"),
    ("gift", "подарки", false, ""),
    ("other", "прочее", false, "");

insert into budget(codename, daily_limit) values ('base', 1600);
