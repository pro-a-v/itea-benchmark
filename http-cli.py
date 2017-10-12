import asyncio
import json
import pickle
import sys
import multiprocessing
import random
import time

from urllib import parse
from aiohttp import ClientSession
from TimerStatistic import Timer


class RESTFailure(Exception):
    def __init__(self, resp):
        self.status = resp.status


class Mattermost(object):
    def __init__(self, loop, team='PersonalTouch'):
        self.base = 'https://enrico.teaches-yoga.com/api/v3/'
        self.loop = loop
        self.session = ClientSession(loop=loop)
        self.tasks = []
        self.headers = {'Content-Type': 'application/json'}
        self._authToken = None

    @property
    def authToken(self):
        return self._authToken

    @authToken.setter
    def authToken(self, value):
        self._authToken = value
        self.headers['Authorization'] = 'Bearer ' + value

    def enqueue(self, method, *args):
        self.tasks.append(asyncio.ensure_future(method(*args)))

    def done(self):
        self.loop.run_until_complete(asyncio.wait(self.tasks))
        results = [each.result() for each in self.tasks]
        self.tasks = []
        print(results)
        return results

    async def login(self, team, loginId, password):
        self.team = team
        self.loginId = loginId
        self.password = password

        url = '{base}users/login'.format(base=self.base)
        payload = {'name': team, 'login_id': loginId, 'password': password}
        async with self.session.post(url, headers=self.headers, data=json.dumps(payload)) as resp:
            if resp.status != 200:
                raise RESTFailure(resp)
            payload = await resp.json()
            return resp.headers['Token'], payload

    async def fetchTeams(self):
        url = '{base}teams/members'.format(base=self.base)
        async with self.session.get(url, headers=self.headers) as resp:
            if resp.stats != 200:
                raise RESTFailure(resp)
            payload = await resp.json()
            return payload


'''
        async with self.session.post(url, headers = self.headers, data = json.dumps(payload)) as resp:
            if resp.status != 200:
                raise RESTFailure(resp)
            response = await resp.json()
            return response'''


def run(pid, delay, userName, password):
    timer = Timer()
    try:
        loop = asyncio.get_event_loop()
        mm = Mattermost(loop)

        timer.begin('delay')
        time.sleep(delay)
        timer.end('delay')

        timer.begin('total')

        # Login
        #
        timer.begin('login')
        mm.enqueue(mm.login, 'PersonalTouch', userName, password)
        mm.authToken, us = mm.done()[0]
        mm.userId = us['id']
        timer.end('login')

        # Fetch Something
        #
        timer.begin('fetchData')
        mm.enqueue(mm.fetchTeams)
        mm.teamId = mm.done()[0][0]['some_data']
        timer.end('fetchData')

        timer.end('total')

    except (RESTFailure,) as exception:
        timer.exceptioned(exception)

    finally:
        mm.session.close()
        loop.close()
    pickle.dump(timer.log, open('perf_user_{}.pkl'.format(pid), 'wb'))


if __name__ == '__main__':

    count = 1
    duration = 10

    lmbda = count / duration
    delays = []
    delay = 0.1
    for each in range(count):
        delays.append(delay)
        delay += random.expovariate(lmbda)

    print(delays)

    processes = []
    for index in range(count):
        customer = 'Sasha'
        p = multiprocessing.Process(target=run, args=(index, delays[index], 'Login', 'Password'))
        p.start()
        processes.append(p)

    with open('perf_times_{}_{}.csv'.format(count, duration), 'w') as output:
        for index, p in enumerate(processes):
            p.join()
            log = pickle.load(open('perf_user_{}.pkl'.format(index), 'rb'))
            if index == 0:
                tags = ['Id'] + [z[1] for z in log]
                output.write(','.join(tags) + '\n')
            output.write(','.join([str(index)] + [str(z[-1]) for z in log]) + '\n')
