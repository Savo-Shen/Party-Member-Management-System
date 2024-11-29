import io
import json
from datetime import datetime

from django.core.serializers import serialize
from django.http import FileResponse
from django.contrib.auth import login, logout, authenticate
from django.middleware.csrf import get_token
from django.http import HttpResponse
from django.utils.encoding import escape_uri_path

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import xlwt

from .models import EvaluationUser, Activity, ActivityImage, UserImage


# 参考: https://blog.csdn.net/weixin_55638841/article/details/133996079
def generate_excel(activity_list):

    # 2.创建一个工作簿(workbook)，并设置编码
    workbook = xlwt.Workbook(encoding='utf-8')

    # style = xlwt.XFStyle()  # 创建一个样式
    #
    # font = xlwt.Font()  # 创建一个文本格式，包括字体、字号和颜色样式
    # font.name = 'SimSun'  # 字体
    # font .charset = xlwt.Font.CHARSET_UTF16  # 字体编码
    # style.font = font

    # 3.创建一个工作表(worksheet)
    worksheet = workbook.add_sheet("党员活动信息")

    # 3.1 设置列宽
    worksheet.col(0).width = 256 * 8  # 8个字符0的宽度
    worksheet.col(1).width = 256 * 12
    worksheet.col(2).width = 256 * 30
    worksheet.col(3).width = 256 * 30
    worksheet.col(4).width = 256 * 30
    worksheet.col(5).width = 256 * 20
    worksheet.col(6).width = 256 * 16

    # 3.2 设置表头行高
    style = xlwt.easyxf('font:height 360;')  # 18pt,类型小初的字号
    row = worksheet.row(0)
    row.set_style(style)

    # 4.写表头部分
    # 4.1 表头数据
    header_list = ['活动ID', '活动名称', '负责党员', '开始时间', '结束时间', '地点', '心得', '活动类型', '是否通过', '是否审核', '审核人', '活动提交时间']

    # 4.3 写表头
    for header_data in enumerate(header_list):
        worksheet.write(0, header_data[0], header_data[1], style)

    # 4.4 写表格内容数据
    for index, row_data in enumerate(activity_list):
        worksheet.write(index + 1, 0, row_data.id)  # 第一行为表头
        worksheet.write(index + 1, 1, row_data.name)
        worksheet.write(index + 1, 2, row_data.student.username)
        worksheet.write(index + 1, 3, row_data.startTime.strftime('%Y-%m-%d %H:%M:%S'))
        worksheet.write(index + 1, 4, row_data.endTime.strftime('%Y-%m-%d %H:%M:%S'))
        worksheet.write(index + 1, 5, row_data.location)
        worksheet.write(index + 1, 6, row_data.description)
        worksheet.write(index + 1, 7, row_data.type)
        worksheet.write(index + 1, 8, row_data.passed)
        worksheet.write(index + 1, 9, row_data.certified)
        if row_data.admin is not None:
            worksheet.write(index + 1, 10, row_data.admin.username)
        worksheet.write(index + 1, 11, row_data.registerTime.strftime('%Y-%m-%d %H:%M:%S'))

        # 表头行高
        row = worksheet.row(index + 1)
        row.set_style(style)

    # 生成文件名称，名称包含法规导出 + 年月日时分秒数字的组合，避免重复
    file_name = '党员活动信息导出{}'.format(datetime.now().strftime(format('%Y-%m-%d %H:%M:%S')))

    # 5.保存文件
    # 5.1 保存到本地文件：保存文件目录级别在项目目录下，与apps同级
    workbook.save("media/files/last.xls")
    # workbook.save("media/files/" + file_name + ".xls")

    # 5.2 保存文件流到内存
    sio = io.BytesIO()
    workbook.save(sio)
    sio.seek(0)

    # 5.3 返回数据给前端
    # 5.3.1 获取文件流，设置文件类型
    response = HttpResponse(sio.getvalue(), content_type='application/vnd.ms-excel')

    # 5.3.2
    # file_name = '党员活动信息导出{}'.format(datetime.now().strftime(format('%Y-%m-%d %H:%M:%S')))

    # 5.3.3 配置Response Headers中`Content-Disposition`信息，支持中文
    response['Content-Disposition'] = "attachment;filename={}.xls".format(escape_uri_path(file_name))

    # 5.3.4 必须将`Content-Disposition`暴露给前端，否则前端获取不到信息
    response['Access-Control-Expose-Headers'] = "Content-Disposition"

    # 5.3.5 返回数据给前端
    response.write(sio.getvalue())

    print("用户导出excel成功")

    return response


class Server(viewsets.GenericViewSet):

    @action(detail=False, methods=['get'])
    def get_token(self, request, *args, **kwargs):
        # print("用户请求了csrf_token")
        csrf_token = get_token(request)
        resp = {
            'status': True,
            'data': csrf_token
        }
        print("用户成功获取csrf_token值：" + csrf_token)
        return Response(resp)

    @action(detail=False, methods=['get'])
    def is_login(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.isAdmin:
                resp = {
                    'status': True,
                    'data': {
                        'userId': request.user.userId,
                        'username': request.user.username,
                        'phone': request.user.phone,
                        'score_test1': request.user.score_test1,
                        'stage': request.user.stage,
                        'isTeacher': request.user.isTeacher,
                        'is_admin': True
                    },
                    'message': '已经登录了'
                }
            else:
                resp = {
                    'status': True,
                    'data': {
                        'userId': request.user.userId,
                        'username': request.user.username,
                        'phone': request.user.phone,
                        'score_test1': request.user.score_test1,
                        'stage': request.user.stage,
                        'isTeacher': request.user.isTeacher,
                        'is_admin': False
                    },
                    'message': '已经登录了'
                }
                print("用户已经登录了")
        else:
            resp = {
                'status': False,
                'message': '还没有登录'
            }
            print("用户还没有登录")
        return Response(resp)

    @action(detail=False, methods=['get'])
    def logout(self, request, *args, **kwargs):
        print("用户请求了登出")
        logout(request)
        resp = {
            'status': True,
            'message': '用户登出成功'
        }
        print("用户登出成功")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def admin_login(self, request, *args, **kwargs):
        print("管理员请求了登录")
        # data = json.loads(request.body)
        data = request.data
        userId = data['adminId']
        password = data['password']
        try:
            user = EvaluationUser.objects.get(userId=userId)
            if user.check_password(password):
                if not user.isAdmin:
                    resp = {
                        'status': False,
                        'message': '非管理员'
                    }
                    print("管理员登录失败，非管理员")
                    return Response(resp)
                login(request, user)
                resp = {
                    'status': True,
                    'message': '登录成功'
                }
                print("管理员登录成功")
            else:
                resp = {
                    'status': False,
                    'message': '密码错误'
                }
                print("管理员登录失败，密码错误")
        except:
            resp = {
                'status': False,
                'message': '管理员不存在'
            }
            print("管理员登录失败，管理员不存在")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def admin_register(self, request, *args, **kwargs):
        print("管理员请求了注册")
        # data = json.loads(request.body)
        data = request.data
        userId = data['adminId']
        username = data['username']
        password = data['password']
        phone = data['phone']
        try:
            admin = EvaluationUser.objects.create_user(userId=userId, username=username, phone=phone, password=password,
                                                       isAdmin=True)
            admin.save()
            resp = {
                'status': True,
                'message': '注册成功'
            }
            print("管理员注册成功")
        except:
            resp = {
                'status': False,
                'message': '注册失败'
            }
            print("管理员注册失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def student_login(self, request, *args, **kwargs):
        print("用户请求了登录")
        data = request.data
        userId = data['studentId']
        password = data['password']
        try:
            user = EvaluationUser.objects.get(userId=userId)
            if user.check_password(password):
                login(request, user)
                resp = {
                    'status': True,
                    'data': {
                        'studentId': user.userId,
                        'username': user.username,
                        'phone': user.phone,
                    },
                    'message': '登录成功',
                }
                print(user.userId + "用户登录成功")
                # return Response(resp).set_cookie("studentId", student.studentId, max_age=3600 * 24 * 1)
            else:
                resp = {
                    'status': False,
                    'message': '密码错误',
                }
                print("用户登录失败，密码错误")
        except:
            resp = {
                'status': False,
                'message': '用户不存在'
            }
            print("用户登录失败，用户不存在")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def student_register(self, request, *args, **kwargs):
        print("用户请求了注册")
        data = request.data
        userId = data['studentId']
        username = data['username']
        password = data['password']
        phone = data['phone']
        try:
            student = EvaluationUser.objects.create_user(userId=userId, username=username, phone=phone)
            student.set_password(password)
            student.save()
            resp = {
                'status': True,
                'message': '注册成功'
            }
            print("用户注册成功")
        except:
            resp = {
                'status': False,
                'message': '注册失败'
            }
            print("用户注册失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def student_update(self, request, *args, **kwargs):
        print("用户请求了更新")
        data = request.data
        userId = data['userId']
        username = data['username']
        phone = data['phone']
        stage = data['stage']
        try:
            student = EvaluationUser.objects.get(userId=userId)
            student.username = username
            student.phone = phone
            student.stage = stage
            student.save()
            resp = {
                'status': True,
                'message': '更新成功'
            }
            print("用户更新成功")
        except:
            resp = {
                'status': False,
                'message': '更新失败'
            }
            print("用户更新失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def change_password(self, request, *args, **kwargs):
        print("用户请求了修改密码")
        data = request.data
        userId = data['userId']
        oldPassword = data['oldPassword']
        newPassword = data['newPassword']
        try:
            user = EvaluationUser.objects.get(userId=userId)
            if user.check_password(oldPassword):
                user.set_password(newPassword)
                user.save()
                resp = {
                    'status': True,
                    'message': '修改成功'
                }
                print("用户修改密码成功")
            else:
                resp = {
                    'status': False,
                    'message': '密码错误'
                }
                print("用户修改密码失败，密码错误")
        except:
            resp = {
                'status': False,
                'message': '用户不存在'
            }
            print("用户修改密码失败，用户不存在")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def delete_student(self, request, *args, **kwargs):
        print("管理员请求了删除学生")
        data = request.data
        studentId = data['studentId']
        try:
            student = EvaluationUser.objects.get(userId=studentId)
            userImages = UserImage.objects.filter(user=student)
            for userImage in userImages:
                userImage.image.delete()
                userImage.delete()  # 删除学生图片

            activities = Activity.objects.filter(student=student)
            for activity in activities:
                activityImages = ActivityImage.objects.filter(activity=activity)
                for activityImage in activityImages:
                    activityImage.image.delete()
                    activityImage.delete()  # 删除活动图片
                activity.delete()  # 删除活动
            student.delete()
            resp = {
                'status': True,
                'message': '删除成功'
            }
            print("管理员删除学生成功")
        except:
            resp = {
                'status': False,
                'message': '删除失败'
            }
            print("管理员删除学生失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def create_activity(self, request, *args, **kwargs):
        print("用户请求了提交活动")
        # data = json.loads(request.body)
        data = request.data
        name = data['name']
        description = data['description']
        startTime = data['startTime']
        endTime = data['endTime']
        location = data['location']
        studentId = data['studentId']
        activityType = data['type']
        try:
            student = EvaluationUser.objects.get(userId=studentId)
            activity = Activity.objects.create(name=name, description=description, startTime=startTime, endTime=endTime,
                                               location=location, student=student, type=activityType)
            activity.save()
            student.score_test1 += 1
            student.save()
            resp = {
                'status': True,
                'message': '提交成功',
                'data': {
                    'activityId': activity.id
                }
            }
            print("用户提交活动成功")
        except:
            resp = {
                'status': False,
                'message': '提交失败'
            }
            print("用户提交活动失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def post_activity_image(self, request, *args, **kwargs):
        print("用户请求了提交活动图片")
        data = request.data
        activityId = data['activityId']
        image = request.FILES['image']
        try:
            activity = Activity.objects.get(id=activityId)
            activityImage = ActivityImage.objects.create(activity=activity, image=image)
            activityImage.save()
            resp = {
                'status': True,
                'message': '提交成功'
            }
            print("用户提交活动图片成功")
        except:
            resp = {
                'status': False,
                'message': '提交失败'
            }
            print("用户提交活动图片失败")
        return Response(resp)

    @action(detail=False, methods=['get'])
    def get_students_list(self, request, *args, **kwargs):
        print("用户请求了获取学生")
        try:
            users = EvaluationUser.objects.all()
            students = users.filter(isAdmin=False)
            resp = {
                'status': True,
                'data': json.loads(serialize('json', students))
            }
            print("用户获取学生列表成功")
        except:
            resp = {
                'status': False,
                'data': '获取失败'
            }
            print("用户获取学生列表失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def get_activities_list(self, request, *args, **kwargs):
        print("用户请求了获取活动")
        data = request.data
        # data = json.loads(request.data)
        studentId = data['studentId']
        startTime = data['startTime']
        endTime = data['endTime']
        certified = data['certified']
        passed = data['passed']
        adminId = data['adminId']
        try:
            activities = Activity.objects.all()
            if studentId != '*' and studentId != '':
                student = EvaluationUser.objects.get(userId=studentId)
                activities = activities.filter(student=student)
            if (startTime != '*' and endTime != '*') and (startTime != '' and endTime != ''):
                activities = activities.filter(startTime__gte=startTime, endTime__lte=endTime)
            if certified != '*' and certified != '':
                activities = activities.filter(certified=certified)
            if passed != '*' and passed != '':
                activities = activities.filter(passed=passed)
            if adminId != '*' and adminId != '':
                admin = EvaluationUser.objects.get(userId=adminId)
                activities = activities.filter(admin=admin)
            resp = {
                'status': True,
                'data': json.loads(serialize('json', activities)),
                'message': '获取活动列表成功'
            }
            print("用户获取活动成功")
        except:
            resp = {
                'status': False,
                'message': '获取活动列表失败'
            }
            print("用户获取活动失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def get_activity_images(self, request, *args, **kwargs):
        print("用户请求了获取活动图片")
        data = request.data
        activityId = data['activityId']
        try:
            activity = Activity.objects.get(id=activityId)
            images = ActivityImage.objects.filter(activity=activity)
            resp = {
                'status': True,
                'data': json.loads(serialize('json', images)),
                'message': '获取成功'
            }
            print("用户获取活动图片成功")
        except:
            resp = {
                'status': False,
                'message': '获取失败'
            }
            print("用户获取活动图片失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def delete_activity(self, request, *args, **kwargs):
        print("用户请求了删除活动")
        data = request.data
        activityId = data['activityId']
        try:
            activity = Activity.objects.get(id=activityId)
            student = activity.student
            activityImages = ActivityImage.objects.filter(activity=activity)
            for activityImage in activityImages:
                activityImage.image.delete()
                activityImage.delete()  # 删除活动图片
            activity.delete()
            student.score_test1 -= 1
            student.save()
            resp = {
                'status': True,
                'message': '删除成功'
            }
            print("用户删除活动成功")
        except:
            resp = {
                'status': False,
                'message': '删除失败'
            }
            print("用户删除活动失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def check_activity(self, request, *args, **kwargs):
        print("用户请求了查看活动")
        data = request.data
        adminId = data['adminId']
        activityId = data['activityId']
        passed = data['passed']
        if passed == 'true':
            passed = True
        else:
            passed = False
        try:
            admin = EvaluationUser.objects.get(userId=adminId)
            activity = Activity.objects.get(pk=activityId)
            if activity.passed:
                resp = {
                    'status': False,
                    'message': '已经审核过了'
                }
                print("用户查看活动失败，已审核")
                return Response(resp)
            activity.passed = passed
            activity.certified = True
            activity.admin = admin
            activity.save()
            resp = {
                'status': True,
                'data': json.loads(serialize('json', [activity])),
                'message': '审核成功'
            }
            print("用户查看活动成功")
        except:
            resp = {
                'status': False,
                'message': '审核失败'
            }
            print("用户查看活动失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def post_user_image(self, request, *args, **kwargs):
        print("用户请求了提交用户图片")
        data = request.data
        userId = data['userId']
        image = request.FILES['image']
        try:
            user = EvaluationUser.objects.get(userId=userId)
            if UserImage.objects.filter(user=user).count() > 0:
                userImage = UserImage.objects.get(user=user)
                userImage.image.delete()
                userImage.delete()
            userImage = UserImage.objects.create(user=user, image=image)
            userImage.save()
            resp = {
                'status': True,
                'message': '提交成功'
            }
            print("用户提交用户图片成功")
        except:
            resp = {
                'status': False,
                'message': '提交失败'
            }
            print("用户提交用户图片失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def get_user_image(self, request, *args, **kwargs):
        print("用户请求了获取活动图片")
        data = request.data
        userId = data['userId']
        try:
            user = EvaluationUser.objects.get(userId=userId)
            images = UserImage.objects.filter(user=user)
            resp = {
                'status': True,
                'data': json.loads(serialize('json', images)),
                'message': '获取成功'
            }
            print("用户获取用户图片成功")
        except:
            resp = {
                'status': False,
                'message': '获取失败'
            }
            print("用户获取用户图片失败")
        return Response(resp)

    @action(detail=False, methods=['post'])
    def export_excel(self, request, *args, **kwargs):
        print("用户请求了导出excel")
        data = request.data
        studentId = data['studentId']
        try:
            if studentId == '*':
                activities = Activity.objects.all()
            else:
                student = EvaluationUser.objects.get(userId=studentId)
                activities = Activity.objects.filter(student=student)

            return generate_excel(activities)
            # resp = {
            #     'status': True,
            #     'data': generate_excel(activities),
            #     'message': '导出成功'
            # }
            # print("用户导出excel成功")
        except:
            resp = {
                'status': False,
                'message': '导出失败'
            }
            print("用户导出excel失败")
        return Response(resp)
