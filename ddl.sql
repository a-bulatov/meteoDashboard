/* талицы и процедуры для сохранения данных о погодже и курсах валют */
create table if not exists currency
(
	d date not null
		constraint currency_pk
			primary key,
	eur numeric(8,4),
	usd numeric(8,4)
);


create schema wether;


create table if not exists today
(
	ntp timestamp not null
		constraint today_pk
			primary key,
	temp_int numeric(7,4),
	temp_ext numeric(7,4),
	pressure numeric(6,3),
	rain smallint,
	mm_hg numeric(5,2)
);


create or replace function from_sensor(_data json) returns json
	language plpgsql
as $$
begin
  /*
   {
   "Time": "2019-12-28 09:41:00",
   "Data": {
    "Pressure": 749.378,
    "Temp": 21.9489,
    "TempExt": -1.5,
    "mmHgExt": 99.9,
    "Rain": 1024,
    "Altitude": 112.462
    },
   "IP": "10.0.0.201",
   "Sensor": "esp8266_08451b00"
   }
  */
  if exists(select 1 from wether.today where ntp=(_data->>'Time')::timestamp) then
      -- запись уже есть
      return json_build_object('result','уже записано');
  else
      if (select ntp::date from wether.today limit 1)<now()::date then
          -- записать средние в другую таблмцу

          truncate table wether.today;
      end if;
      insert into wether.today(ntp, temp_int, temp_ext, pressure, rain, mm_hg)
      values (
             (_data->>'Time')::timestamp,
             (_data->'Data'->>'Temp')::numeric(7,4),
             (_data->'Data'->>'TempExt')::numeric(7,4),
             (_data->'Data'->>'Pressure')::numeric(6,3),
             (_data->'Data'->>'Rain')::smallint,
             (_data->'Data'->>'mmHgExt')::numeric(5,2)
      );
  end if;
  return null;
end
$$;