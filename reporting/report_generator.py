'''
Created on Oct 16, 2018

@author: agagaleza
'''
from datetime import datetime
from xml.sax import saxutils
from reporting.report_constants import ReportConstants
import logging
from common.config.constant import Constant

class ReportGenerator(object):
    __version__ = "0.1"
    logger = logging.getLogger(__name__)
    '''
    classdocs
    '''
    


    def __init__(self,stream):
        self.title = ReportConstants.DEFAULT_TITLE
        self.description = ReportConstants.DEFAULT_DESCRIPTION
        self.stream = stream

    def get_attributes(self, json_data):
        start_time = datetime.utcnow()
        duration = 0
        try:
            start_time = json_data[0]['Scenario_0']["start"]
            self.logger.info(start_time)
            end_time = int(json_data[-1]["Scenario_"+ str(len(json_data) - 1)]["stop"])
            self.logger.info(end_time)
            duration = end_time - start_time
            status = []
            passed = 0
            failure = 0
            error = 0
            for x in json_data:
                for scenario in x:
                    result = ReportConstants.STATUS[x[scenario]["status"]]
                    if result == Constant.PASSED:
                        passed = passed +1
                    elif result == Constant.FAILED:
                        failure = failure +1
                    else:
                        error = error +1
            status.append('Pass %s'    % passed)
            status.append('Failure %s'    % failure)
            status.append('Error %s'    % error)

            if status:
                status = ' '.join(status)
            else:
                status = 'none'
        except KeyError:
            self.logger.info('Empty results')
        except IndexError:
            self.logger.info('Empty results')
        return [
            ('Start Time', self.format_unix_timestamp(start_time / 1000, '%Y-%m-%dT%H:%M:%SZ')),
            ('Duration', str(self.convert_miliseconds(duration))),
            ('Status', status),
        ]

    def generateReport(self, result):
        report_attrs = self.get_attributes(result)
        generator = 'ReportGenerator %s' % ReportGenerator.__version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = ReportConstants.HTML_TMPL % dict(
            title=saxutils.escape(self.title),
            generator = generator,
            stylesheet=stylesheet,
            heading=heading,
            report=report,
            ending=ending,
        )
        self.stream.write(output.encode('utf8'))
        
    def _generate_stylesheet(self):
        return ReportConstants.STYLESHEET_TMPL
    
    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = ReportConstants.HEADING_ATTRIBUTE_TMPL % dict(
                    name=saxutils.escape(name),
                    value=saxutils.escape(value),
                )
            a_lines.append(line)
        heading = ReportConstants.HEADING_TMPL % dict(
            title=saxutils.escape(self.title),
            parameters=''.join(a_lines),
            description=saxutils.escape(self.description),
        )
        return heading
    
    def _generate_report(self, json_data):
        
        rows = []
        scenario_id = 0
        total_passed = 0
        total_failed = 0
        total_error = 0
        for scenario in json_data:
            np = nf = ne = 0
            for step in scenario['Scenario_' + str(scenario_id)]['steps']:
                if step['status'] == Constant.PASSED: np += 1
                elif step['status'] == Constant.FAILED: nf += 1
                else: ne += 1
        

            row = ReportConstants.REPORT_CLASS_TMPL % dict(
                style=ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
                desc=scenario['Scenario_' + str(scenario_id)]['name'],
                count=np + nf + ne,
                Pass=np,
                fail=nf,
                error=ne,
                cid='c%s' % (scenario_id + 1),
            )
            rows.append(row)
            step_id = 1
            for step in scenario['Scenario_' + str(scenario_id)]['steps']:
                self._generate_report_test(rows, scenario_id,step, step_id, step_id)
                step_id +=1
            scenario_id +=  1
            total_passed +=np
            total_failed += nf
            total_error += ne
        report = ReportConstants.REPORT_TMPL % dict(
            test_list=''.join(rows),
            count=str(total_passed + total_failed + total_error),
            Pass=str(total_passed),
            fail=str(total_failed),
            error=str(total_error),
            )
          
        return report

    def _generate_report_test(self, rows, cid,step, tid, name):
        status = ReportConstants.STATUS[step["status"]]
        has_output = bool(status != Constant.PASSED)
        tid = status + ' t%s.%s' % (cid+1,tid)
        doc = step["name"]
        desc = doc and ('%s: %s' % (name, doc)) or name
        tmpl = has_output and ReportConstants.REPORT_TEST_WITH_OUTPUT_TMPL or ReportConstants.REPORT_TEST_NO_OUTPUT_TMPL
        uo = ''
        ue = ''
        try:
            uo = step['statusDetails']['message']
            ue = step['statusDetails']['trace']
        except KeyError:
            pass

        script = ReportConstants.REPORT_TEST_OUTPUT_TMPL % dict(
            id = tid,
            output = saxutils.escape(uo+ue),
        )
        class_str = 'none'
        if status == "passed":
            class_str = 'hiddenRow'
            
        style_str = 'none'
        if status == 'failed':
            style_str = 'failCase'
        elif status != 'passed':
            style_str = 'errorCase'
        else:
            style_str = 'passCase'
        row = tmpl % dict(
            tid = tid,
            Class = class_str,
            style = style_str,
            desc = desc,
            script = script,
            status = status,
        )
        rows.append(row)
        if not has_output:
            return
        
    def _generate_ending(self):
        return ReportConstants.ENDING_TMPL

    def format_unix_timestamp(self, unixtime, formatstr):
        return str(datetime.utcfromtimestamp(unixtime).strftime(formatstr))   


    def convert_miliseconds(self, ms):
        s=ms/1000
        m,s=divmod(s,60)
        h,m=divmod(m,60)
        d,h=divmod(h,24)
        s=10
        return "%d days %02d:%02d:%02d" % (d,h,m,s) 
    




