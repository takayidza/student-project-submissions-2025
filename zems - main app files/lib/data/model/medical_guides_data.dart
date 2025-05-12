import 'medical_guide_model.dart';

final List<MedicalGuideModel> medicalGuides = [
  MedicalGuideModel(
    title: 'CPR for Adults',
    description: 'Step-by-step guide for performing cardiopulmonary resuscitation on adults.',
    expandedInfo: '''- Ensure the scene is safe
- Check for responsiveness by tapping the person and shouting "Are you okay?"
- Call emergency services or have someone else do it
- Place the person on their back on a firm surface
- Kneel beside the person\'s chest
- Place the heel of one hand on the center of the chest (lower half of sternum)
- Place your other hand on top and interlock fingers
- Position shoulders directly over hands, keep arms straight
- Compress chest at least 2 inches (5 cm) deep at a rate of 100-120 compressions per minute
- Allow complete chest recoil between compressions
- Minimize interruptions in compressions
- Continue until emergency services arrive or the person shows signs of life''',
  ),
  MedicalGuideModel(
    title: 'CPR for Children',
    description: 'Proper techniques for performing CPR on children ages 1-12.',
    expandedInfo: '''- Ensure the scene is safe
- Check for responsiveness by tapping and shouting
- If no response, have someone call emergency services
- Place the child on their back on a firm surface
- Give 2 rescue breaths: tilt head back slightly, lift chin, pinch nose, cover mouth with yours and blow for 1 second each
- Use only one hand for chest compressions (center of chest)
- Press down about 2 inches at a rate of 100-120 compressions per minute
- After 30 compressions, give 2 rescue breaths
- Continue cycles of 30 compressions and 2 breaths
- If alone, perform 5 cycles (about 2 minutes) before calling emergency services''',
  ),
  MedicalGuideModel(
    title: 'CPR for Infants',
    description: 'Special considerations when performing CPR on infants under 1 year.',
    expandedInfo: '''- Ensure the scene is safe
- Check for responsiveness by tapping the foot and watching for movement
- If no response, have someone call emergency services
- Place the infant on their back on a firm surface
- Give 2 rescue breaths: tilt head to neutral position, cover infant\'s mouth and nose with your mouth
- Use two fingers to deliver compressions to the center of the chest, just below the nipple line
- Press down about 1.5 inches at a rate of 100-120 compressions per minute
- After 30 compressions, give 2 rescue breaths
- Continue cycles of 30 compressions and 2 breaths
- If alone, perform 5 cycles (about 2 minutes) before calling emergency services''',
  ),
  MedicalGuideModel(
    title: 'Choking in Adults',
    description: 'How to help an adult who is choking with step-by-step instructions.',
    expandedInfo: '''- Recognize signs of choking: inability to talk, coughing, or breathing, clutching the throat
- Ask "Are you choking?" - if the person nods yes and cannot speak, act immediately
- Stand behind the person and wrap your arms around their waist
- Make a fist with one hand and place it above the navel
- Grab your fist with your other hand
- Press hard into the abdomen with quick, upward thrusts
- Continue until the object is expelled or the person becomes unconscious
- If unconscious, lower them to the ground and begin CPR
- Each time you open the airway to give breaths, look for the object in the mouth and remove it if visible''',
  ),
  MedicalGuideModel(
    title: 'Choking in Children',
    description: 'Adjusted techniques for helping a choking child (age 1-12).',
    expandedInfo: '''- Confirm the child is choking by asking "Are you choking?" 
- If they cannot speak, cough, or breathe, stand behind the child
- Place your fist just above their navel
- Grasp your fist with your other hand
- Give quick, upward abdominal thrusts
- Continue until the object is expelled or the child becomes unconscious
- If unconscious, begin CPR
- Look in the mouth before each breath and remove any visible objects
- Use less force than with adults when performing abdominal thrusts
- For a small child, you may need to kneel to properly position yourself''',
  ),
  // ... Add the rest of the guides here ...
]; 