import requests
import re
import json
import subprocess
import os

# 视频爬虫
class VideoSpider:

    # 初始化
    def __init__(self,url):
        # 视频列表的URL
        # 获取多条数据修改成 range(1,100) 以此类推
        self.url_list = [ url + str(i) for i in range(1) ]
        # 视频存放路径
        self.video_save_path = 'video/'
        if os.path.exists(self.video_save_path) == False:
            os.makedirs(self.video_save_path)


    @staticmethod
    def get_response(url):
        domain = re.findall('https://(.*?)/',url)[0]
        referer = f"https://{domain}/"
        headers = {
            "domain" :domain,
            "referer": referer,
            "Sec-Ch-Ua-Platform": "Windows",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url=url,headers=headers)
        except Exception as e:
            print(e)
            return None

        return response
    

    # 分析视频的html获取视频地址、音频地址、标题
    @staticmethod
    def parse_video_html(response) -> dict:
        video_data = re.findall('<script>window.__playinfo__=(.*?)</script>',response.text)[0]
        title_id = re.findall('h1 data-title="(.*?)" title=.*</h1>',response.text)[0]
        # json 序列化
        json_data = json.loads(video_data)
        audio_url= json_data['data']['dash']['audio'][0]['baseUrl']
        video_url = json_data['data']['dash']['video'][0]['baseUrl']
        
        video_json = {
            'title':title_id,
            'audio_url':audio_url,
            'video_url':video_url
        }
        return video_json 

    # 保存视频
    def save_video(self,title,audio_url,video_url):
        audio = self.get_response(audio_url).content
        video = self.get_response(video_url).content
        filename = self.video_save_path + title
        try:
            with open(filename + '.mp4',mode='wb') as f:
                f.write(video)
            with open(filename +'.mp3',mode='wb') as f:
                f.write(audio)
            
            # 将视频与音频合并
            COMMAND = f'ffmpeg -i {filename}.mp4 -i {filename}.mp3 -c:v copy -c:a aac -strict experimental {filename}_new.mp4'
            dev_null = open(os.devnull,'w')
            subprocess.call(COMMAND,shell=True,stdout=dev_null)

            # 删除无用音视频文件
            self.remove_video(filename + '.mp4')
            self.remove_video(filename + '.mp3')
            
        except Exception as e:
            print(e)

    # 删除无用视频文件
    def remove_video(self,filename):
        os.remove(filename)


    # 获取需要获取的视频地址列表
    def get_video_url_list(self):
        data = []
        for url in self.url_list:
            response = self.get_response(url)
            j = json.loads(response.text)

            # 遍历获取视频地址
            for item in j["data"]["item"]:
                data.append(item["uri"])

        return data
    
    # 总入口
    def run(self):
        for url in self.get_video_url_list():
            response = self.get_response(url=url)     
            video_json = self.parse_video_html(response)   
            self.save_video(video_json['title'],video_json['audio_url'],video_json['video_url'])


if __name__ == "__main__":
    url = 'https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd?display_id='
    spider = VideoSpider(url=url)
    spider.run()

