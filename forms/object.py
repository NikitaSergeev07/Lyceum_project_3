from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import  SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired

class ObjectForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    price = FloatField('Цена')
    category = SelectField('Категория', choices=[("Телеграмм каналы"), ("Сайты"), ("ВК сообщества")])
    city = SelectField("Город", choices=[('Курск'), ('Москва'), ('Санкт-Петербург')])
    submit = SubmitField('Применить')
