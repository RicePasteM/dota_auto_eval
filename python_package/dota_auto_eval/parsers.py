from typing import Dict, Any
import re

class ResultParser:
    """Base class for result parser"""
    
    def parse(self, html_content: str) -> Dict[str, Any]:
        """
        Parse HTML format result content
        
        Args:
            html_content: HTML format result content
            
        Returns:
            Dict[str, Any]: Parsed result dictionary
        """
        return str

class V1Task1Parser(ResultParser):
    """DOTA Task1 Result Parser"""
    
    def parse(self, html_content: str) -> Dict[str, Any]:
        """
        Parse DOTA Task1 results
        
        Args:
            html_content: HTML format result content
            
        Returns:
            Dict[str, Any]: Parsed result dictionary containing:
                - voc_map: VOC mAP value
                - voc_ap: AP values dictionary for each class
                - coco_ap50: COCO AP50 value
                - coco_ap75: COCO AP75 value
                - coco_map: COCO mAP value
                - submission_info: Submission information dictionary
        """
        result = {}
        
        try:
            # Parse VOC metrics
            voc_map_match = re.search(r'<li><b>mAP</b>: ([\d.]+)</li>', html_content)
            if voc_map_match:
                result['voc_map'] = float(voc_map_match.group(1))
            
            # Parse AP for each class
            ap_match = re.search(r'<li><b>ap of each class</b>: (.+?)</li>', html_content)
            if ap_match:
                ap_text = ap_match.group(1)
                ap_pairs = [pair.strip() for pair in ap_text.split(',')]
                voc_ap = {}
                for pair in ap_pairs:
                    name, value = pair.split(':')
                    voc_ap[name] = float(value)
                result['voc_ap'] = voc_ap
            
            # Parse COCO metrics
            coco_matches = {
                'coco_ap50': r'<li><b>AP50</b>: ([\d.]+)</li>',
                'coco_ap75': r'<li><b>AP75</b>: ([\d.]+)</li>',
                'coco_map': r'<li><b>mAP</b>: ([\d.]+)</li>'
            }
            
            for key, pattern in coco_matches.items():
                match = re.search(pattern, html_content)
                if match:
                    result[key] = float(match.group(1))
            
            # Parse submission information
            submission_info = {}
            info_items = {
                'Description': 'description',
                'Username': 'username',
                'Institute': 'institute',
                'Emailadress': 'email',
                'TeamMembers': 'team_members'
            }
            
            for label, key in info_items.items():
                pattern = rf'<li>{label}: (.+?)</li>'
                match = re.search(pattern, html_content)
                if match:
                    submission_info[key] = match.group(1)
            
            result['submission_info'] = submission_info
            
        except Exception as e:
            print(f"Parsing error: {str(e)}")
            print(f"Raw HTML content: {html_content}")
            raise
        
        return result 